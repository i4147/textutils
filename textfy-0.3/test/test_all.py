import random
import sys
from time import sleep


sys.path.append("../textfy")

from textfy import Textfy, send_msg


@Textfy()
def test():
    num_episode = 10

    total_sleep_time = 0
    for i in range(num_episode):
        sleep_time = random.randint(3, 6)
        total_sleep_time += sleep_time

        print(f"[{i}]")
        print("sleep_time:", sleep_time)

        sleep(sleep_time)

        loss, acc = random.random(), random.random() * 100
        print("loss:", loss)
        print("acc:", acc)

        if i == (num_episode // 2):
            send_msg(f"loss: {loss:.4f} | acc: {acc:.4f}")

    return {"loss": loss, "acc": acc}


if __name__ == "__main__":
    test()
