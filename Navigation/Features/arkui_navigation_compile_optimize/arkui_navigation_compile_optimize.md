# 1. 冗余头文件整理

请检索[owner_mapping](./owner_mapping.json)文件，针对其中owner为@arkui_navigation的文件做分析、检查。具体要求如下：

1. 列出每个文件所有引用的.h头文件，并按照对应头文件被实际使用的次数从小到大排序
2. 针对使用次数很少（小于10次。临界点指标根据被分析文件的行数自适应变化，500行时为最大值）的.h文件，给出修改建议（例如前向声明）
3. 针对使用次数较多（10次及以上，临界点指标根据被分析文件的行数自适应变化，500行时为最大值）的.h文件，给出修改建议

由于文件较多，请在与本文档同级目录下新建一个`header_analysis_result`目录。

对于每次的分析结果，请在`header_analysis_result`目录下新建`result_YYMMDD_time`目录存放。单次结果格式为json，具体如下：

```json
  "file_name": { // file_name为被分析文件的名称，基于openharmony根目录给出相对路径，例如`foundation/arkui/ace_engine/frameworks/core/components_ng/pattern/navigation/navigation_pattern.h`
    "0_used_headers": [
        {
            "file_name": "demo.h",
            "optimized": "直接删除"
        },
        {
            "file_name": "demo2.h",
            "optimized": "直接删除"
        },
    ],
    "little_used_headers": [ // 使用次数较少
        {
            "file_name": "lite_use_demo0.h",
            "used_count": 1,
            "optimized": "使用次数较少时的优化建议，例如：前向声明，实际调用移动到cpp"
        },
        {
            "file_name": "lite_use_demo.h",
            "used_count": 3,
            "optimized": "使用次数较少时的优化建议，例如：前向声明，实际调用移动到cpp"
        },
    ],
    "many_times_used_headers": [ // 使用次数较多
        {
            "file_name": "lite_use_demo0.h",
            "used_count": 11,
            "optimized": "*使用次数较多时的优化建议*"
        },
        {
            "file_name": "lite_use_demo.h",
            "used_count": 20,
            "optimized": "不建议删除" // 使用次数相当多时不建议删除，除非都是简单使用，可以通过前向声明的方式优化。
        },
    ]
  },
```

考虑json太大时影响阅读体验，请对`result_YYMMDD_time`目录下的输出结果进行拆分，保证每个子文件结果不大于10000行（需保证json的完整性，不允许内容截断）。

拆分的子文件命名格式为：`result_part_number.json`，例如`result_part_1.json`。

# 2. 冗余头文件整改

请根据最新的冗余头文件整理的结果（存放在./header_analysis_result/，子目录含有时间戳），对其中调用次数较少的头文件进行整改。

## 2.1 未使用头文件排序

请根据最新的冗余头文件整理的结果（存放在./header_analysis_result/，子目录含有时间戳），将0_used_headers数组的最大的top 50个文件写入到`top_0_used_header_files_no_ut.json`（该文件写入到最新的冗余头文件整理的结果目录下）。格式与数据源一致。

> 说明：不包括测试的test文件

## 2.2 删除未使用的头文件

对于某些`被分析文件`，可直接删除0_used_headers数组中的文件。然而，这样可能会导致某些cpp编译异常（由于间接依赖）。为了保证编译的正确性，请做如下操作：

1. 在openharmony的根目录（foundation的父目录）执行./limited_fast_build.sh，如果遇到编译报错，请=对应的cpp补充缺少的.h文件（往往是被删除的.h）。
2. 重复操作直到编译通过

> 说明：仅允许删除指定的`被分析文件`中的头文件引用。只允许在修补编译的前提下修改`被分析文件`之外的文件。

# 3. 量化优化数据

在openharmony的根目录下（foundation的父目录）执行`python main.py -d ./`，该指令会根据最新的编译结果生成结果报告。等待报告生成后，帮我计算如下两点：

1. 增量优化：相比于最近一次的分析报告，本次报告中@arkui_navigation责任田的代码膨胀量减少了多少
2. 全量优化：相比于最新一次的分析报告，本次报告中@arkui_navigation责任田的代码膨胀量减少了多少

此后，在./foundation/arkui/ace_engine/目录下进行代码提交，commit按照如下格式：
```
git commit -sm "navigation compile analysis YYMMDD, increment: xx, full-increment: yy"
```
其中YYMMDD为当前时间，xx为先前计算的`增量优化`，yy为先前计算的`全量优化`

# 4. 自动化执行

## 4.1 自动化删除未使用头文件

请按照如下的流程执行：

1. 执行[冗余头文件整理](#1-冗余头文件整理)
2. 等待步骤1结束后，根据结果执行[未使用头文件排序](#21-未使用头文件排序)
3. 等待步骤2结束后，根据`top_0_used_header_files_no_ut.json`做如下操作：
    3.1 取`top_0_used_header_files_no_ut.json`中未被处理过的10个文件，执行[删除头文件](#22-删除未使用的头文件)；
    3.2 等待3.1编译通过后，执行[量化优化数据](#3-量化优化数据)；
    3.3 等待3.2完成后，将本次处理的10个文件在`top_0_used_header_files_no_ut.json`标记为已处理；
    3.4 等待3.3完成后，检查是否还存在未处理的文件。如全部处理完毕，结束步骤3；如未全部处理完毕，从步骤3.1开始重复。
4. 根据3.2的数据，输出本次流程总的优化数据

## 4.2 自动化删除未使用头文件（轻量）

> 说明：使用已存在的`top_0_used_header_files_no_ut.json`

1. 根据最新的（依据父目录的时间戳）`top_0_used_header_files_no_ut.json`做如下操作：
    1.1 取`top_0_used_header_files_no_ut.json`中未被处理过的10个文件，执行[删除头文件](#22-删除未使用的头文件)；
    1.2 等待1.1编译通过后，执行[量化优化数据](#3-量化优化数据)；
    1.3 等待1.2完成后，将本次处理的10个文件在`top_0_used_header_files_no_ut.json`标记为已处理；
    1.4 等待1.3完成后，检查是否还存在未处理的文件。如全部处理完毕，结束步骤3；如未全部处理完毕，从步骤3.1开始重复。
2. 根据1.2的数据，输出本次流程总的优化数据