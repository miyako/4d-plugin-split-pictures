![version](https://img.shields.io/badge/version-18%2B-EB8E5F)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20|%20win-64&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-split-pictures)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-split-pictures/total)

# 4d-plugin-split-pictures
Split a composite 4D picture (field or variable) into an array of native formats. 

## Syntax

```4d
SPLIT PICTURES (picture;types;images)
```

Parameter|Type|Description
------------|------------|----
picture|PICTURE|
types|ARRAY TEXT|
images|ARRAY PICTURE|

## Examples

```
ALL RECORDS([Table_1])
SPLIT PICTURES ([Table_1]Field_2;$types;$images)
```

![](https://github.com/miyako/4d-plugin-split-pictures/blob/master/images/1.png)
