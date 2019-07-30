# coding=utf-8
# Created by Meteorix at 2019/7/22

import time
import os
from tqdm import tqdm
from service_streamer import ThreadedStreamer, Streamer
from service_streamer import RedisWorker, GpuWorkerManager
from bert_model import Model


def main():
    max_batch = 128
    model = Model()
    text = "Who was Jim Henson ? Jim Henson was a puppeteer"
    streamer = Streamer(model.predict, batch_size=max_batch, max_latency=0.1, worker_num=4, cuda_devices=(0, 1, 2, 3), model=model)
    # streamer = ThreadedStreamer(model.predict, batch_size=max_batch, max_latency=0.1)
    num_times =13000

    class GpuWorkers(GpuWorkerManager):

        def gpu_worker(self, index, gpu_num):
            os.environ["CUDA_VISIBLE_DEVICES"] = str(index % gpu_num)
            RedisWorker(model.predict, 64, max_latency=0.1).run_forever()

    """
    t_start = time.time()
    for i in tqdm(range(num_times)):
        output = model.predict([text])
    t_end = time.time()
    print('model prediction time', t_end - t_start)
    """
    model.bert.to("cuda")
    t_start = time.time()
    inputs = [text] * num_times
    for i in tqdm(range(num_times // max_batch + 1)):
        output = model.predict(inputs[i*max_batch:(i+1)*max_batch])
        print(len(output))
    t_end = time.time()
    print('model batch prediction time', t_end - t_start)

    t_start = time.time()
    xs = []
    for i in range(num_times):
        future = streamer.submit([text])
        xs.append(future)

    for future in tqdm(xs):  # 先拿到所有future对象，再等待异步返回
        output = future.result(timeout=20)
    t_end = time.time()
    print('streamer prediction time', t_end - t_start)

    # streamer._worker_process.join()
    # GpuWorkers().run_workers_forever(worker_num=8, gpu_num=4)


if __name__ == '__main__':
    main()

