#!/bin/bash
declare -a targets=(
 [5000]="Jinja2 - Python"
 [5001]="Mako - Python"
 [5002]="Tornado - Python"
 [5002]="Django - Python"
 [5002]="(Code eval) - Python"
 [5005]="(Code exec) - Python"
 [5020]="Smarty - PHP"
 [5021]="Smarty (secure mode) - PHP"
 [5022]="Twig - PHP"
 [5023]="(Code eval) - PHP"
 [5051]="FreeMarker - Java"
 [5052]="Velocity - Java"
 [5053]="Thymeleaf - Java "
 [5061]="Jade - Nodejs"
 [5062]="Nunjucks - JavaScript"
 [5063]="doT - JavaScript"
 [5065]="Dust - JavaScript"
 [5066]="EJS - JavaScript"
 [5067]="(Code eval) - JavaScript"
 [5068]="VueJs - JavaScript"
 [5080]="Slim - Ruby"
 [5081]="ERB - Ruby"
 [5082]="(Code eval) - Ruby"
 [5090]="go - go"
 [6001]="Input rendered in other location"
 [6002]="Rendering result not visible to attacker"
 [6003]="Input inserted in the middle of template code math operations"
 [6005]="Input inserted in the middle of template code text"
 [6004]="Non Vulnerable"
 [6010]="\{ \} Python Eval"
 [6011]="$\{ \} Python Eval"
 [6012]="\{\{ \}\} Python Eval"
 [6013]="<%= %> Python Eval ERB"
 [6014]="#\{ \} Python Eval"
 [6015]="\{\{= \}\} Python Eval"
 [6020]="\{ \} Ruby Eval"
 [6021]="$\{ \} Ruby Eval"
 [6022]="\{\{ \}\} Ruby Eval YBNE Nunjucks"
 [6023]="<%= %> Ruby Eval Erb"
 [6024]="#\{ \} Ruby Eval"
 [6025]="\{\{= \}\} Ruby Eval"
)

cd /zap/wrk/

export file=/zap/wrk/all.yml

/zap/zap.sh -silent -addoninstall ascanrulesAlpha -cmd

echo "section: All URLs" > $file
echo "details:" >> $file

for i in "${!targets[@]}"; do
  echo "var PORT = $i;" > ssti-score.js
  echo "var TITLE = \"${targets[$i]}\";" >> ssti-score.js
  cat ssti-score-main.js >> ssti-score.js
  echo "$i  -> ${targets[$i]}";
  export port=$i
  pwd
  /zap/zap.sh -silent -autorun /zap/wrk/ssti.yaml -cmd
  cat $file
  sleep 5
done

pass=`grep -c "any: Pass" $file`
fail=`grep -c "any: FAIL" $file`

let "score = ($pass * 100) / ($pass + $fail)"

echo "score: $score%" >> $file

echo Pass: $pass
echo Fail: $fail
echo Score: $score%
