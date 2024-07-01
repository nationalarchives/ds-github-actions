#!/bin/sh

inotifywait \
  $1 \
  --monitor \
  --recursive \
  -e close_write \
  --timefmt '%Y-%m-%dT%H:%M:%S' \
  --format '%T %w %f %e' \
  | \
while read datetime dir filename event; do
  echo "Event: $datetime $dir$filename $event"
  echo "Now, we could pass $datetime $dir $filename and $event to some other command."

  echo "Here's the extensionless filename:" ${filename%.*}
  echo "And the extension if needed:" ${filename##*.}

  regex_pattern="(\/sftp-data\/)(.*?)(\/)"
  if [[ "$dir" =~ $regex_pattern ]]; then
    key=${BASH_REMATVH[2]}
  fi

  aws s3 cp $dir$filename s3://da-sftp-intake/$key/$filename
  #python3 /app/phono.py --custom $dir$filename $dir${filename%.*}.txt /tmp/${filename%.*}
done
