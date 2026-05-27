from fastapi import APIRouter, HTTPException, Query

from app.services.recommendation_service import (
    get_recommended_packages,
    get_recommended_activities,
    get_similar_packages,
    get_trending_packages,
)

router = APIRouter(prefix="/recommendations",tags=["Recommendations"])

@router.get("/packages")
def recommend_packages(
    user_id: int = Query(..., description="User ID to Get recommendations for"),
    limit: int = Query(...,description="number of recommendations to return"),
):
    try:
        results = get_recommended_packages(user_id, limit)
        
        return{
            "user_id": user_id,
            "total": len(results),
            "recommendations": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/activities")
def recommend_activities(
    user_id: int = Query(..., description="USER ID to Get recommendations for"),
    limit: int = Query(..., description="number of recommendations to return"),
):
    try:
        results = get_recommended_activities(user_id, limit)
        
        return{
            "user_id": user_id,
            "total": len(results),
            "recommendations": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/similar")
def similar_packages(
    package_id: int = Query(..., description="Package ID to find similar packages for"),
    limit: int = Query(6, description="number of similar packages to return"),
):
    try:
        results = get_similar_packages(package_id, limit)
        
        return{
            "package_id": package_id,
            "total": len(results),
            "similar_packages": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/trending")
def trending_packages(
    limit: int = Query(10,description="Number of trending packages to return"),
):
    try:
        results = get_trending_packages(limit)
        
        return{
            "total": len(results),
            "trending_packages": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 