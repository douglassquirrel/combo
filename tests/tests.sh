echo "subscribing to combo.test topic"
set -x; curl --include --request POST http://$1:8080/topics/combo.test/subscription ; set +x; echo

echo "publishing fact on combo.test topic"
set -x; curl --include --request POST --header "Content-Type: application/json" \
             --data-binary '{ "test": "aaa", "foo": 111 }' \
             http://$1:8080/topics/combo.test/facts ; set +x; echo

echo "publishing another fact on combo.test topic"
set -x; curl --include --request POST --header "Content-Type: application/json" \
             --data-binary '{ "test": "bbb", "foo": 222 }' \
	     http://$1:8080/topics/combo.test/facts ; set +x; echo

echo "fetching all topics"
set -x; curl --include http://$1:8080/topics ; set +x; echo

echo "fetching last 10 facts for combo.test topic"
set -x; curl --include http://$1:8080/topics/combo.test/facts ; set +x; echo

echo "fetching facts for combo.test topic after id 2"
set -x; curl --include http://$1:8080/topics/combo.test/facts?after_id=2 ; set +x; echo

