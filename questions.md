*  `asyncio`是在如何在单线程中实现并发的.它究竟使哪些阻塞的操作变成了非阻塞的操作,根本上省下的时间是在哪里省下的?

* 我们为什么需要`yield`和`async`/`await`?`yield`解决了什么,`async`/`await`又解决了什么?

* `EventLoop`是如何工作的?`asyncio`的实现原理是什么?为什么`asyncio`需要配套的库如`aiomysql`,`aiohttp`才能如预期地工作?这些库与同步的库如`mysqlclient`,`requests`本质上有什么区别?它们做了什么?