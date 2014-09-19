set -x

echo "fetching queue for combo.test topic"
curl --include --request POST http://$1:8080/topics/combo.test/queue

echo "publishing fact on combo.test topic"
curl --include --request POST --header "Content-Type: application/json" --data-binary '{ "test": "aaa", "foo": 111 }' http://$1:8080/topics/combo.test

echo "publishing another fact on combo.test topic"
curl --include --request POST --header "Content-Type: application/json" --data-binary '{ "test": "bbb", "foo": 222 }' http://$1:8080/topics/combo.test

echo "fetching all topics"
curl --include http://$1:8080/topics

echo "fetching last 10 facts for combo.test topic"
curl --include http://$1:8080/topics/combo.test

echo "fetching facts for combo.test topic since id 2"
curl --include http://$1:8080/topics/combo.test?from_id=2

