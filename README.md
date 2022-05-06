# matrix_srun_manager

This script checks nodes on matrix and determines if the requested resource type is actualizable, and returns a srun command to fulfill the request.

Consider using adding like this in your bashrc. 

```
function request (){
    N_GPU=1
    N_CPU=8
    TIME=8
    EXCLUDE=""
    VRAM=0
    RAM=16
    ARCHI=None
    while getopts ":g:c:e:t:v:r:a:" opt; do
        case $opt in
        g) N_GPU=$OPTARG
        ;;
        c) N_CPU=$OPTARG
        ;;
        e) EXCLUDE=$OPTARG
        ;;
        t) TIME=$OPTARG
        ;;
        v) VRAM=$OPTARG
        ;;
        r) RAM=$OPTARG
        ;;
        a) ARCHI=$OPTARG
        ;;
        \?) echo "Invalid option -$OPTARG" >&2
        exit 1
        ;;
        esac
    done
    #N_GPU=${3-1}
    #N_CPU=${4-8}
    ALLOC=$(python __PATH_TO_MATRIX_SRUN_MANAGER__/get_alloc.py --num_cpu=$N_CPU --num_gpu=$N_GPU --a
    SRUN_COMMAND=$(echo $ALLOC | grep RESULT)
    # SRUN_COMMAND="srun -n1 --cpus-per-gpu $((N_CPU / N_GPU)) --gres=gpu:$N_GPU --mem=${RAM}g -m arbit
    echo $ALLOC
    eval ${SRUN_COMMAND:7}
    #eval $SRUN_COMMAND
}
```