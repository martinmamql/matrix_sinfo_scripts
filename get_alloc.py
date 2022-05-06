import argparse
import os 
import yaml
from sinfo_parsing import get_free_nodes

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--num_cpu', type=int, default=6, help='num cpu')
parser.add_argument('--num_gpu', type=int, default=1, help='num gpu')
parser.add_argument('--archi', type=str, default=None, help='architecture of GPU')
parser.add_argument('--vram', type=int, default=0, help='VRAM')
parser.add_argument('--exclude', type=str, default=None, help='exclude features')
parser.add_argument('--ram', type=int, default=8, help='RAM')
parser.add_argument('--time', type=int, default=24, help='time')

args = parser.parse_args()

if args.archi.strip().lower() == "none":
    args.archi = None


if args.exclude is not None:
    args.exclude = args.exclude.replace('"',"")
    exclude = set(args.exclude.split(","))
else:
    exclude = set()

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, "cluster_info.yaml"), "r") as stream:
    try:
        cluster_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

if args.vram is not None:
    vram_permissible_cluster_list = [info['cluster'] for info in cluster_info['gpu_clusters'] if info['vram']>=args.vram]

architecture = {}

for i,archi in enumerate(cluster_info['archi']):
    architecture[archi] = i

if args.archi is not None and args.archi.lower() not in architecture.keys():
    print("Something is wrong. Make sure that --archi is in {}".format(architecture.keys()))

free_list = get_free_nodes()
# print(cluster_info)
# permissible_cluster_list = []
# exclude_cluster_list = [node['node'] for node in get_nodes() if node['partition']=='facunix']

# permissible_nodes = [node['node'] for node in get_nodes() if node['partition']!='facunix']

mynode = None
for name, node in free_list.items():
    archi_node = cluster_info['gpus'][node['gpu_type']]['archi']
    if name in cluster_info['exclude_features'].keys():
        exclude_feats = set(cluster_info['exclude_features'][name])
    else:
        exclude_feats = set()
    if node['partition'] not in cluster_info['permissible_partitions']:
        continue
    elif args.ram is not None and node['free_mem'] < args.ram * 1000:
        continue
    elif args.vram is not None and node['nodelist'] not in vram_permissible_cluster_list:
        continue
    elif node['gpu_num']<args.num_gpu or node['cpus']<args.num_cpu:
        continue
    elif args.archi is not None and architecture[archi_node]<architecture[args.archi.lower()]:
        continue
    elif node['timelimit']<args.time:
        continue
    elif len(exclude.intersection(exclude_feats))>0:
        continue
    else:
        mynode = node
        break

if mynode is not None:
    srun_command = "srun -n1 --cpus-per-gpu {} --gres=gpu:{} --mem={}g --nodelist={} -t {}:00:00 --pty zsh".format(
        args.num_cpu//args.num_gpu, args.num_gpu, args.ram, mynode['nodelist'], args.time
        )
else:
    print("WARNING: No nodes match request, falling back to general srun command")
    srun_command = 'echo "No free nodes available, consider waiting"; '
    srun_command = srun_command + "srun -n1 --cpus-per-gpu {} --gres=gpu:{} --mem={}g -t {}:00:00 --pty zsh".format(
        args.num_cpu//args.num_gpu, args.num_gpu, args.ram, args.time
        )

print("RESULT:{}".format(srun_command))
# for cluster in cluster_info['gpu_clusters']:
#     if "matrix-{}".format(cluster['cluster']) not in permissible_nodes:
#         continue
#     if args.vram is not None and cluster['vram']<args.vram:
#         exclude_cluster_list.append("matrix-{}".format(cluster['cluster']))
#         continue
#     if 'exclude_features' in cluster.keys() and len(exclude.intersection(set(cluster['exclude_features'])))>0:
#         exclude_cluster_list.append("matrix-{}".format(cluster['cluster']))
#         continue
#     if cluster['gpu_num'] < args.num_gpu:
#         exclude_cluster_list.append("matrix-{}".format(cluster['cluster']))
#         continue
#     permissible_cluster_list.append("matrix-{}".format(cluster['cluster']))


# print(','.join(permissible_cluster_list))
