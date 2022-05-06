# functions for extraction information from sinfo
# 2018 Colleen Rooney
import subprocess
import re

def node_pretty(node_number, compute=True):
    """Given a string 'node_number' pads node number with 0s"""
    # this is because of how our nodes are named, need to change if nodes are
    # named differently compute nodes have 3 digits, phi and himem have 2
    length = 3 if compute else 2
    while len(node_number) < length:
        node_number = '0' + node_number
    return node_number


def sep_nodes(node_type, partition, node_range, node_list=[]):
    """Given a string 'node_type' (compute, phi, himem) a partition (medium,
    long, phi etc.) and a string 'node_range' (001-031, 095) appends a
    dictionary with the name stored under the key 'name' and the partition
    stored under the key 'partition' of all the nodes in the range, to a list
    (default empty list) and returns the list"""
    start_end = node_range.split('-')

    # janky fix... should really use regex to handle name of default partition
    # specific to coeus
    if partition == "medium*": partition = "medium"

    compute = False if node_type != "compute" else True
    if len(start_end) == 2:
        for node in range(int(start_end[0]), int(start_end[1]) + 1):
            # specific to coeus 
            node_number = node_pretty(str(node), compute)
            node_list.append({'node':node_type + node_number,
                                'partition':partition})

    elif len(start_end) == 1:
        node_number = node_pretty(str(start_end[0]), compute)
        node_list.append({'node':node_type + node_number,
                            'partition':partition})

def convert_to_M(string):
    if string.isnumeric():
        return int(string)
    elif string.lower() == "n/a":
        return 0
    unit = string[-1]
    value = int(string[:-1])
    if unit=="G":
        value=int(value)*1000
    else:
        value=int(value)
    return value

def print_table(info_dict):
    from tabulate import tabulate
    data = []
    keys = ["nodelist", "cpus", "free_mem", "gpu_num", "gpu_type",'timelimit', "partition"]
    for n,v in info_dict.items():
        data.append([v[k] for k in keys])
    data = sorted(data, key=lambda x : "{}{}".format(x[keys.index('partition')], x[keys.index('gpu_num')]))
    print(tabulate(data, headers=keys))


def get_free_nodes(partition='', state='idle'):
    """Returns the idle nodes using the SLURM sinfo command. If a partition
    is specified only idle nodes of that partition will be returned"""
    # get data from sinfo
    sinfo_out = subprocess.Popen('sinfo -e --Node -O All'.split(' '), stdout=subprocess.PIPE)
    squeue_keys_format = "%g|%N|%C|%m|%b|%P|%o"
    squeue_keys = "group,nodelist,cpus,memory,gpu_num,partition,command"
    squeue_out = subprocess.Popen('squeue -h -t R -o "{}"'.format(squeue_keys_format).split(' '), stdout=subprocess.PIPE)
    sinfo_out = sinfo_out.communicate()[0].decode().split('\n')#[1:]
    squeue_out = squeue_out.communicate()[0].decode().split('\n')#[1:]
    # print(squeue_out)

    sinfo_keys = [x.strip().lower() for x in sinfo_out[0].split('|')]
    node_list = {}
    for line in sinfo_out[1:]:
        if line.strip() == '':
            continue
        info = [x.strip() for x in line.split('|')]
        info = dict(list(zip(sinfo_keys, info)))
        info['free_mem'] = convert_to_M(info['free_mem'])
        gres = info['gres'].split(':')
        info['gpu_num'] = int(gres[-1])
        info['cpus'] = int(info['cpus'])
        info['gpu_type'] = gres[1]
        info['timelimit'] = int(info['timelimit'].split('-')[0])*24 if info['timelimit']!='infinite' else 8
        if info['nodelist'] in node_list.keys() and info['partition']=='facunix':# and int(info['prio_job_factor']) <= int(node_list[info['nodelist']]['prio_job_factor']):
            continue
        else:
            node_list[info['nodelist']]=info
    
    usage_list = {}
    squeue_keys = [x.strip().lower() for x in squeue_keys.split(',') if x.strip()!=""]
    for line in squeue_out:
        if line.strip() == '':
            continue
        info = [x.strip() for x in line.split('|')]
        info = dict(list(zip(squeue_keys, info)))
        if info['nodelist'] in usage_list.keys():
            usage_list[info['nodelist']].append(info)
        else:
            usage_list[info['nodelist']] = [info]
    # print(node_list)

    free_list = node_list.copy()
    for node,usages in usage_list.items():
        if node not in free_list.keys():
            print("node {} fucked".format(node))
            continue
        else:
            for usage in usages:
                free = free_list[node]
                free['cpus'] = max(0, int(free['cpus']) - int(usage['cpus']))
                gpu_num = int(usage['gpu_num'].split(':')[-1]) if usage['gpu_num']!='N/A' else 0
                free['gpu_num'] = max(0, free['gpu_num'] - gpu_num)
                free['free_mem'] = max(0, free['free_mem'] - convert_to_M(usage['memory']))
                # print(free.keys())
                free_list[node] = free
    print_table(free_list)

    # nodes = []
    # for line in lines:
    #     partition = line['partition']
    #     m = re.findall('matrix-\d-(?:\[[\d,]*\]|\d+)', line['nodes'])

    #     for matched in m:
    #         node_list = matched[matched.find("["):].replace('[', '').replace(']', '').split(',')
    #         node_type = matched[:matched.find("[")]
    #         for node in node_list:
    #             nodes.append({'node':"{}{}".format(node_type, node), 'partition': partition})

    return free_list