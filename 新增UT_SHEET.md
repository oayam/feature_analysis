# base

请先阅读如下的代码

`./frameworks/core/components_ng/pattern/overlay/sheet_presentation_pattern.cpp`

分析其中未被覆盖的关键分支，生成对应的UT。尽可能覆盖所有的逻辑分支，以做到兼容性

> 说明：
>
> 1. 当前库上已存在UT：`sheet_presentation_test*ng.cpp`，生成UT时可以参考已存在的UT的格式，但要避免生成重复的、已存在的UT
> 2. 生成UT新开一个文件`sheet_presentation_test_new.cpp`
> 3. 生成600行
