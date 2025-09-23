#!/usr/bin/env bash

CURRFILE=`realpath "$0"`
CURRDIR=`dirname "$CURRFILE"`

sudo apt install python3-gi python3-gi-cairo gir1.2-gtksource-3.0 gir1.2-vte-2.91

echo "#!/usr/bin/env bash" > /usr/bin/idz
echo "python3 $CURRDIR/main.py \"\$@\"" >> /usr/bin/idz
chmod a+x /usr/bin/idz
cat /usr/bin/idz
