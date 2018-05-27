#!/usr/bin/python

import os

strToSearch="<h2>This application was deployed using AWS CodeDeploy.</h2>"

strToReplace="<h2>This application was deployed using the AWS CodeDeploy " + os.environ['APPLICATION_NAME'] + " application using the " + os.environ['DEPLOYMENT_GROUP_NAME'] + " deployment group by " + os.environ['DEPLOYMENT_GROUP_ID'] +  " deployment group id and was generated by an " + os.environ['LIFECYCLE_EVENT'] + " script during the revision ID " + os.environ['DEPLOYMENT_ID'] + " deployment.</h2>"

fp=open("/var/www/html/release.html","r")
buffer=fp.read()
fp.close()

fp=open("/var/www/html/release.html","w")
fp.write(buffer.replace(strToSearch,strToReplace))
fp.close()