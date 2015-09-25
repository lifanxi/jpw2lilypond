# jpw2lilypond
Convert JP-Word format to Lilypond/jianpu format

```shell
$ iconv -f utf-16 jpw.txt > test.txt # 转utf-16到utf-8
$ python2.7 main.py -f test.txt -t test.jianpu # 转成jianpu-ly需要的格式
$ python2.7 jianpu-ly.py < test.jianpu > test.ly # 用jianpu-ly转成LilyPond的标准格式
$ lilypond test.ly # 用LilyPond生成PDF和MIDI文件
```
