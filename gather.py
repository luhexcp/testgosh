#coding:utf-8
import json
import sys
import jenkins
import requests
import os
import re

protect = sys.argv[1]
dict_desc = {'Deadcode' : '无用片段','GoLint' : '风格问题','CopyCheck':'重复检查','Cyclo':'圈复杂度'}

JENKINS_SERVER_URL = 'http://localhost:8080'
USER = 'admin'
PASSWORD = 'admin'
DATA_GATHER_URL = 'http://10.92.184.144:5000/open_api/v1/backend_ci_result'
LEGAL_SCORE = 50

def load_data_json():
    file_path = os.environ.get('WORKSPACE') + "/" + os.environ.get('JOB_NAME') + "/data.json"
    f = open(file_path)
    jsonResult['data'] = json.load(f)
    close(f)
    file_path = os.environ.get('WORKSPACE') + "/" + os.environ.get('JOB_NAME') + "/htmlData.json"
    f = open(file_path)
    jsonResult['htmlData'] = json.load(f)
    close(f)
    return jsonResult

def loadOutPut():
    server = jenkins.Jenkins(JENKINS_SERVER_URL,USER,PASSWORD)
    job_info = server.get_job_info(sys.argv[1])
    print(job_info)
    last_build = job_info['lastBuild']
    build_info['commit_id']
    result = server.get_build_console_output(sys.argv[1],last_build)
    return result


def get_build_info(job_name, last_build_num):
    server = get_service()
    try:
        ci_build = server.get_build_info(job_name, int(last_build_num))
    except JenkinsException as e:
        print("get build job info error! job num: %s, last build num: %s"%({job_name},{last_build_num}))


    actions = ci_build['actions']
    parameters_action = None
    for data in actions:
        if data.get('_class', None) == 'hudson.model.ParametersAction':
            parameters_action = data
            break

    if not parameters_action:
        return None

    build_info = {
        'result': ci_build['result'],
        'build_time': datetime.fromtimestamp(int(ci_build['timestamp']) / 1000),
        'change_id': None,
        'commit_id': None,
    }
    parameters = parameters_action['parameters']
    for parameter in parameters:
        if parameter['name'] == 'GERRIT_CHANGE_ID':
            build_info['change_id'] = parameter['value']
        if parameter['name'] == 'GERRIT_PATCHSET_REVISION':
            build_info['commit_id'] = parameter['value']

    return build_info


def get_json_result():
    json = load_data_json()
    metrics = json['data']['metrics']
    d = {}
    res = {}
    warnings_count = 0
    for metric in metrics:
        name = metrics[metric]['name']
        summaries = metrics[metric]['summaries']
        count = 0
        for module in summaries:
            if summaries[module]['errors']:
                count += len(summaries[module]['errors'])
                warnings_count += count
        d[name] = count
    res['score'] = json['data']['score']
    res['warnings'] = d
    res['warnings_count'] = warnings_count

    res['line_count'] = json['htmlData']['CodeCount']['summary']['line_count']
    coverage = 0 if json['htmlData']['CodeTest']['summary']['code_cover'] is None else json['htmlData']['CodeTest']['summary']['code_cover']
    res['coverage'] = string.atof(coverage) / 100

    return res

def getLastResult():
    return {'score' : 58}

def get_service():
    return jenkins.Jenkins(JENKINS_SERVER_URL, USER, PASSWORD)


def get_result():
    jsonResult = get_json_result()
    result = {}
    result['score'] = jsonResult['score']
    result['line_count'] = jsonResult['line_count']
    result['coverage'] = jsonResult['coverage']
    # lastResult = getLastResult()
    # change_score = jsonResult['score'] - lastResult['score']
    # change_score_str =  "提高%s分"%change_score
    rst = ""
    for metric in dict_desc:
        name = dict_desc[metric]
        count = jsonResult['warnings'][metric]
        rst += "%s出现%s次，"%(name, count)
    result['warnings_detail'] = json.dumps(jsonResult['warnings'])
    result['warnings_count'] = jsonResult['warnings_count']
    reporter_url = "http://localhost:8080/job/%s/result/" % protect
    str = "本次提交质量分数%s分，其中%s详情见 %s" % (jsonResult['score'], rst, reporter_url)
    result['desc'] = str
    return result

def send(ci_id,commit_id,code_score,test_case_coverage,code_lines_count,is_legal,warnings_count,warnings_detail):
    r = requests.post(DATA_GATHER_URL, data = {'job_id':ci_id, 'commit_id':commit_id, 'code_score':code_score, 'test_case_coverage':test_case_coverage,
                                    'code_lines_count':code_lines_count, 'is_legal':is_legal,'warnings_count':warnings_count, 'warnings_detail':warnings_detail})
    r.raise_for_status()
    resp = r.json()
    print(resp)

if __name__ == '__main__':
    job_name = os.environ.get('JOB_NAME')
    print("### job name ###\n")
    print(job_name + "\n")
    ci_id = os.environ.get('CI_ID')
    print("### job id ###\n")
    print(ci_id + "\n")
    server = get_service()
    try:
        job_info = server.get_job_info(job_name)
    except JenkinsException as e:
        print("get job info error! job name: %s" % ({job_name}))
    last_build_num = job_info['lastBuild']['number']
    print("### last_build_num ###\n")
    print(last_build_num + "\n")

    build_info = get_build_info(job_name, last_build_num)
    print("### build_info ###\n")
    print(build_info + "\n")
    commit_id = build_info['commit_id']
    result = get_result()
    print("### reporter result ###\n")
    print(result + "\n")
    code_score = result['score']
    test_case_coverage = result['coverage']
    code_lines_count = result['lines_count']
    is_legal = code_score > LEGAL_SCORE
    warnings_count = result['warnings_count']
    warnings_detail = result['warnings_detail']
    send(ci_id,commit_id,code_score,test_case_coverage,code_lines_count,is_legal,warnings_count,warnings_detail)
    print(result['desc'])

