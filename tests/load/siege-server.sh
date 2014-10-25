# Requires the siege load test program
# See http://www.joedog.org/siege-home/
URLS=/tmp/urls.txt
echo "SERVER=$1" > $URLS
cat urls-template.txt >> $URLS
siege -i -f $URLS
