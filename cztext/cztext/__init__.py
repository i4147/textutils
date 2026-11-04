#coding:utf-8
from cztext import overflow_ellipsis as _overflow_ellipsis,cn_len_more_than,len_more_than

def overflow_ellipsis(text,width):
    if text:
        return _overflow_ellipsis(text,width)
    else:
        return ""

if __name__ == "__main__":
    test_string = """[BetterExplained]如何有效地记忆与学习

逃出你的肖申克（二）：仁者见仁智者见智？从视觉错觉到偏见

编程的首要原则(s)是什么？

[BetterExplained]为什么你应该（从现在开始就）写博客

[BetterExplained]书写是为了更好的思考

[BetterExplained]亲密关系中的冲突解决

独立日

逃出你的肖申克（一）：一定要亲身经历了之后才能明白？

逃出你的肖申克（一）：为什么一定要亲身经历了之后才能明白？
英国政府用网路优化，推动「关键温和人士」改善网路暴力

LivingSocial收购BuyYourFriendADrink，求得了一条更直接的获利模式

当iPhone遇见另一支iPhone可以如何「正经玩」？用Bump「撞」出友情吧

4/16课后报告：NET-MBA网路成功案例分享四堂课《获利篇》

全球最大的小珠珠网路商店，竟在美国西北角偏远小森林

网路又爆红了男女英雄各一枚，但我心属另两位男女「配角」

一生的浪人，从烦恼之中不断开出新的窗

Scanwiches和ThisIsWhyYoureFat以拍色情照片态度来拍「食物」，二个月爆红！

4/9课后报告：NET-MBA网路成功案例分享四堂课《行销篇》
My Brute对战小游戏经过４点精心设计，一周内爆红全地球！
"""
    for i in range(1000):
        print cn_len_more_than(test_string,250)
    
    test_string = test_string.split("\n")
    for w in range(100,200,20):
        for i in test_string:
            if i.strip():
                for xxx in range(1000):
                    overflow_ellipsis(i, w)
                print overflow_ellipsis(i, w)

