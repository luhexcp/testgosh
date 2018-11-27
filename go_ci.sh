#!/bin/bash
echo "current workspace：" $WORKSPACE
echo "GOROOT: ${GOROOT}"
echo "PATH: ${PATH}"
export GOPATH=$WORKSPACE
echo "GOPATH: ${GOPATH}"

mkdir -p $GOPATH/{src,pkg,bin}

project_name=$(echo $GERRIT_URL | awk -F/ '{print $NF}' | sed 's/.git//g')
echo ${project_name}

#go install
ln -f -s $WORKSPACE $GOPATH/src/$project_name

export PATH=$PATH:$GOPATH/bin
export GOBIN=$GOPATH/bin
cd $GOPATH/src/$project_name
go get
go install
export PATH=$PATH:/root/goWork/bin
goreporter -p ./ -r ./ -e src,vendor -f html
#gometalinter.v2 ./... --disable-all  --enable=test --enable=errcheck --enable=structcheck --enable=safesql --enable=vet --checkstyle > checkstyle.xml
python gather.py