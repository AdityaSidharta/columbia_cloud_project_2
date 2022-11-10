##!/bin/bash

rm -f lf2.zip
rm -f function/lambda_function.py
cp lambda/lf2.py function/
mv function/lf2.py function/lambda_function.py
cd function
zip ../lf2.zip lambda_function.py
cd ../package
zip -r ../lf2.zip .
