from fastapi import APIRouter
import os
from buho_back.models import CreateDealRequest, DeleteDealRequest
from buho_back.services.storage.file_management import (
    get_deals_for_user,
    create_deal_for_user,
    delete_deal_for_user,
)


router = APIRouter()


@router.get("/")
def get_deals(user: str = "user"):
    deals = get_deals_for_user(user)
    return {"deals": deals}


@router.post("/delete")
def create_deal(body: DeleteDealRequest, user: str = "user"):
    deal = body.deal
    message = delete_deal_for_user(user, deal)
    print(message)
    return {"message": message}


@router.post("/create")
def create_deal(body: CreateDealRequest, user: str = "user"):
    deal = body.deal
    message = create_deal_for_user(user, deal)
    print(message)
    return {"message": message}
