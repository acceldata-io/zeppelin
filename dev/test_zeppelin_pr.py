#!/usr/bin/env ambari-python-wrap
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# This utility creates a local branch from specified pullrequest, to help the test and review
# You'll need to run this utility from master branch with command 
#
#    dev/test_zeppelin_pr.py [#PR]
#
# then pr[#PR] branch will be created.
#

from __future__ import print_function
import sys, os, subprocess, json, codecs

if sys.version_info[0] == 2:
    from urllib import urlopen
else:
    from urllib.request import urlopen

if len(sys.argv) == 1:
    print("usage) " + sys.argv[0] + " [#PR]")
    print("   eg) " + sys.argv[0] + " 122")
    sys.exit(1)


pr=sys.argv[1]
githubApi="https://api.github.com/repos/apache/zeppelin"

reader = codecs.getreader("utf-8")
prInfo = json.load(reader(urlopen(githubApi + "/pulls/" + pr)))
if "message" in prInfo and prInfo["message"] == "Not Found":
    sys.stderr.write("PullRequest #" + pr + " not found\n")
    sys.exit(1)

prUser=prInfo['user']['login']
prRepoUrl=prInfo['head']['repo']['clone_url']
prBranch=prInfo['head']['label'].replace(":", "/")
print(prBranch)

# create local branch
exitCode = os.system("git checkout -b pr" + pr)
if exitCode != 0:
    sys.exit(1)

# add remote repository and fetch
exitCode = os.system("git remote remove " + prUser)
exitCode = os.system("git remote add " + prUser + " " + prRepoUrl)
if exitCode != 0:
    sys.stderr.write("Can not add remote repository.\n")
    sys.exit(1)

exitCode = os.system("git fetch " + prUser)
if exitCode != 0:
    sys.stderr.write("Can't fetch remote repository.\n")
    sys.exit(1)


currentBranch = subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True).rstrip().decode("utf-8")

print("Merge branch " + prBranch + " into " + currentBranch)

rev = subprocess.check_output("git rev-parse " + prBranch, shell=True).rstrip().decode("utf-8")
prAuthor = subprocess.check_output("git --no-pager show -s --format=\"%an <%ae>\" " + rev, shell=True).rstrip().decode("utf-8")
prAuthorDate = subprocess.check_output("git --no-pager show -s --format=\"%ad\" " + rev, shell=True).rstrip().decode("utf-8")

prTitle = prInfo['title']
prBody = prInfo['body']

commitList = subprocess.check_output("git log --pretty=format:\"%h\" " + currentBranch + ".." + prBranch, shell=True).rstrip().decode("utf-8")
authorList = []
for commitHash in commitList.split("\n"):
    a = subprocess.check_output("git show -s --pretty=format:\"%an <%ae>\" "+commitHash, shell=True).rstrip().decode("utf-8")
    if a not in authorList:
        authorList.append(a)

commitMsg = prTitle + "\n"
if prBody :
  commitMsg += prBody + "\n\n"
for author in authorList:
    commitMsg += "Author: " + author +"\n"
commitMsg += "\n"
commitMsg += "Closes #" + pr + " from " + prBranch + " and squashes the following commits:\n\n"
commitMsg += subprocess.check_output("git log --pretty=format:\"%h [%an] %s\" " + currentBranch + ".." + prBranch, shell=True).rstrip().decode("utf-8")

exitCode = os.system("git merge --no-commit --squash " + prBranch)
if exitCode != 0:
    sys.stderr.write("Can not merge\n")
    sys.exit(1)
    
exitCode = os.system('git commit -a --author "' + prAuthor + '" --date "' + prAuthorDate + '" -m"' + commitMsg + '"')
if exitCode != 0:
    sys.stderr.write("Commit failed\n")
    sys.exit(1)

os.system("git remote remove " + prUser)
print("Branch " + prBranch + " is merged into " + currentBranch)
