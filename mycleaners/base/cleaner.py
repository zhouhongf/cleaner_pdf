# 从数据库中取出manual
# 根据manual的文件类型，应用不同的方法，读取manual的content
import asyncio
import aiofiles
from datetime import datetime
from signal import SIGINT, SIGTERM
from config.log import Logger
from collections import namedtuple
from database.backends import MongoDatabase
import os
from config import Config, SpiderCount
from utils.file_util import divide_pdf_tables_text, divide_word_tables_text, divide_html_tables_text
import cchardet
import re

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class Cleaner:
    logger = Logger(level='error').logger
    file_path = Config.FILE_DIR

    Manual = namedtuple("Manual", "ukey content content_type")
    suffix_file = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.zip', '.rar', '.tar', '.bz2', '.7z', '.gz']

    metadata: dict = None
    kwargs: dict = None

    worker_numbers: int = 3
    worker_tasks: list = []

    success_counts: int = 0
    failure_counts: int = 0

    def __init__(self, name=None, loop=None, is_async_start: bool = False, cancel_tasks: bool = True, **kwargs):
        if name is not None:
            self.name = name
        elif not getattr(self, 'name', None):
            raise ValueError("%s must have a name" % type(self).__name__)
        self.bank_name = getattr(self, 'bank_name', None)                   # 如果没有定义bank_name, 则使用start_bank_name()方法启动
        self.other_file_type = getattr(self, 'other_file_type', '.other')   # 子类在实例化时，在类元素中定义保存在数据库中的.other类型manual,应该保存为何种类型的文件

        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()

        self.metadata = self.metadata or {}
        self.kwargs = self.kwargs or {}
        self.cancel_tasks = cancel_tasks
        self.is_async_start = is_async_start

        # 数据流向是从Mongo到Mongo
        self.mongo = MongoDatabase()
        mongo_db = self.mongo.db()
        self.collection_manual = mongo_db['MANUAL']
        self.collection_outline = mongo_db['OUTLINE']
        self.collection_wealth = mongo_db['WEALTH']
        self.collection_spider_count = mongo_db['spider_count']

    @classmethod
    async def async_start(cls, loop=None, cancel_tasks: bool = True, **kwargs):
        loop = loop or asyncio.get_event_loop()
        cleaner_ins = cls(loop=loop, is_async_start=True, cancel_tasks=cancel_tasks, **kwargs)
        await cleaner_ins._start()
        return cleaner_ins

    @classmethod
    def start(cls, loop=None, close_event_loop=True, **kwargs):
        loop = loop or asyncio.new_event_loop()
        cleaner_ins = cls(loop=loop, **kwargs)
        cleaner_ins.loop.run_until_complete(cleaner_ins._start())
        cleaner_ins.loop.run_until_complete(cleaner_ins.loop.shutdown_asyncgens())
        if close_event_loop:
            cleaner_ins.loop.close()
        return cleaner_ins

    async def _start(self):
        print('【=======================================启动：%s=========================================】' % self.name)
        start_time = datetime.now()

        for signal in (SIGINT, SIGTERM):
            try:
                self.loop.add_signal_handler(signal, lambda: asyncio.ensure_future(self.stop(signal)))
            except NotImplementedError:
                print(f"{self.name} tried loop.add_signal_handler but not implemented on this platform.")

        await self.start_master()

        end_time = datetime.now()
        spider_count = SpiderCount(name=self.name, time_start=start_time, time_end=end_time, success=self.success_counts, failure=self.failure_counts)
        self.collection_spider_count.insert_one(spider_count.do_dump())
        print(spider_count)
        print('----------- 用时：%s ------------' % (end_time - start_time))

    # 为队列queue的生产者，将handle_manual(manual_in)方法 加入队列queue中
    async def start_master(self):
        if self.bank_name:
            async for manual_in in self.process_bank_name():
                self.queue.put_nowait(self.handle_manual(manual_in))
        else:
            async for manual_in in self.start_bank_name():
                self.queue.put_nowait(self.handle_manual(manual_in))

        workers = [asyncio.ensure_future(self.start_worker()) for index in range(self.worker_numbers)]
        for worker in workers:
            self.logger.info(f"Worker started: {id(worker)}")
        await self.queue.join()              # 阻塞至队列中所有的元素都被接收和处理完毕。当未完成计数降到零的时候， join() 阻塞被解除。

        if not self.is_async_start:          # 在async_start()方法中, 如果实例化cleaner时is_async_start=True，则等待执行stop()方法
            await self.stop(SIGINT)
        else:
            if self.cancel_tasks:            # 在async_start()方法中, 如果实例化cleaner时cancel_tasks=True, 则取消前面的tasks, 执行当前异步启动的task
                await self._cancel_tasks()

    # 根据bank_name，从MongoDB数据库Manual中，找出还没有被处理的manual内容, 保存为文件形式，并返回Manual实例
    async def process_bank_name(self):
        condition = {'bank_name': self.bank_name, 'status': 'undo'}
        results = self.collection_manual.find(condition)
        for one in results:
            ukey = one['ukey']
            content = one['content']
            content_type = one['file_suffix']
            if content_type == '.other':
                content_type = self.other_file_type

            # 保存为文件, 用于handle_manual()方法中 打开 文件 进行解析
            filename = os.path.join(self.file_path, ukey + content_type)
            if content:
                if not os.path.exists(filename):
                    print('文件夹中没有%s, 现在保存' % filename)
                    try:
                        with open(filename, 'wb') as file:
                            file.write(content)
                    except:
                        encoding = cchardet.detect(content)['encoding']
                        content = content.decode(encoding, errors='ignore')             # content从byte对象变为str对象
                        with open(filename, 'w') as file:
                            file.write(content)
            # 返回一个Manual实例
            yield self.Manual(ukey=ukey, content=content, content_type=content_type)

    # 如果没有定义bank_name, 则使用start_bank_name()方法启动， 自定义起点入口，可以返回一个manual_in，或者manual_in集合
    async def start_bank_name(self):
        manual_in = self.Manual(ukey='', content='', content_type='')
        yield manual_in

    async def divide_tables_text(self, filename):
        content_type = os.path.splitext(filename)[-1]
        tables, text = None, None
        try:
            if content_type == '.pdf':
                tables, text = divide_pdf_tables_text(filename)
            elif content_type == '.doc' or content_type == '.docx':
                tables, text = divide_word_tables_text(filename)
            elif content_type == '.html' or content_type == '.htm' or content_type == '.shtml' or content_type == '.shtm':
                tables, text = divide_html_tables_text(filename)
            else:
                print('============================ 特殊文件类型，无法解析: %s ================================' % filename)
        except Exception as e:
            self.logger.error('提取%s文件内容时出错：%s' % (filename, e))
        return tables, text

    async def handle_manual(self, manual_in: Manual):
        # 一个文件名，即对应一个ukey
        ukey = manual_in.ukey
        content_type = manual_in.content_type
        filename = os.path.join(self.file_path, ukey + content_type)
        # 从该文件中，成功解析出来的ukey集合
        list_ukey = []

        if manual_in.content:
            tables, text = await self.divide_tables_text(filename)
            if tables or text:
                list_ukey = await self.parse_manual(ukey=ukey, tables=tables, text=text)
                await self._process_manual(ukey=ukey, list_ukey=list_ukey)

        return ukey, list_ukey

    async def parse_manual(self, ukey, tables, text):
        list_ukey = []
        return list_ukey

    async def _process_manual(self, ukey, list_ukey):
        if ukey in list_ukey:
            await self.process_manual_success(ukey, list_ukey)
        else:
            await self.process_manual_failure(ukey, list_ukey)

    async def process_manual_success(self, ukey, list_ukey):
        self.success_counts += 1

    async def process_manual_failure(self, ukey, list_ukey):
        self.failure_counts += 1

    # 为队列queue的消费者，从队列中取出handle_manual(manual_in)方法并执行
    async def start_worker(self):
        while True:
            request_item = await self.queue.get()
            self.worker_tasks.append(request_item)
            if self.queue.empty():
                results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
                for task_result in results:
                    if not isinstance(task_result, RuntimeError) and task_result:
                        ukey, list_ukey = task_result
                self.worker_tasks = []          # 执行完本轮任务后，self.worker_tasks重新还原为空集合
            self.queue.task_done()              # 每当消费协程调用 task_done() 表示这个条目item已经被回收，该条目所有工作已经完成，未完成计数就会减少。

    async def stop(self, _signal):
        await self._cancel_tasks()
        self.loop.stop()

    async def _cancel_tasks(self):
        tasks = []
        for task in asyncio.Task.all_tasks():
            if task is not asyncio.tasks.Task.current_task():
                tasks.append(task)
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def save_wealth(self, dict_wealth: dict):
        list_ukey = []
        for k, v in dict_wealth.items():
            data = v.do_dump()

            risk = data['risk']
            term = data['term']
            amount_buy_min = data['amount_buy_min']
            rate_min = data['rate_min']
            rate_max = data['rate_max']

            pattern_num = re.compile(r'\d+')
            pattern_float = re.compile(r'[0-9]+\.?[0-9]*')

            if risk:
                res = pattern_num.fullmatch(str(risk))
                if not res:
                    data['risk'] = 0
            else:
                data['risk'] = 0

            if term:
                res = pattern_num.fullmatch(str(term))
                if not res:
                    data['term'] = 0
            else:
                data['term'] = 0

            if amount_buy_min:
                res = pattern_num.fullmatch(str(amount_buy_min))
                if not res:
                    data['amount_buy_min'] = 0
            else:
                data['amount_buy_min'] = 0

            if rate_min:
                res = pattern_float.fullmatch(str(rate_min))
                if not res:
                    data['rate_min'] = 0.0
            else:
                data['rate_min'] = 0.0

            if rate_max:
                res = pattern_float.fullmatch(str(rate_max))
                if not res:
                    data['rate_max'] = 0.0
            else:
                data['rate_max'] = 0.0

            condition = {'_id': data['_id']}
            manual = self.collection_manual.find(condition)
            if manual:
                data['file_type'] = manual['file_suffix']

            print('准备保存的wealth是：', data)
            result = self.mongo.do_insert_one(self.collection_wealth, condition, data)
            if result:
                list_ukey.append(result['_id'])
        return list_ukey
