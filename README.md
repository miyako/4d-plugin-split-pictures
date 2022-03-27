# 4d-plugin-split-pictures
Split a composite 4D picture (field or variable) into an array of native formats. 

## Syntax

```
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
