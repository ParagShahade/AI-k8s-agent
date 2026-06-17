from fastapi import APIRouter

from kubernetes.kubeconfig import list_contexts

router = APIRouter()


@router.get("/clusters")
async def get_clusters():
    return list_contexts()
