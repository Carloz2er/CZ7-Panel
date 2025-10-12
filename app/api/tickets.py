from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.ticket import Ticket, TicketMessage
from app.schemas.ticket import Ticket as TicketSchema, TicketCreate, TicketMessageCreate

router = APIRouter()

@router.post("/", response_model=TicketSchema, status_code=status.HTTP_201_CREATED)
def create_ticket(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ticket_in: TicketCreate
):
    """
    Create a new ticket with an initial message.
    """
    new_ticket = Ticket(title=ticket_in.title, owner_id=current_user.id)
    db.add(new_ticket)
    db.flush()  # Flush to get the new_ticket.id

    first_message = TicketMessage(
        content=ticket_in.initial_message,
        ticket_id=new_ticket.id,
        author_id=current_user.id
    )
    db.add(first_message)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/", response_model=List[TicketSchema])
def read_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve tickets for the current user.
    """
    tickets = db.query(Ticket).filter(Ticket.owner_id == current_user.id).offset(skip).limit(limit).all()
    return tickets

@router.get("/{ticket_id}", response_model=TicketSchema)
def read_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific ticket by ID.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return ticket

@router.post("/{ticket_id}/messages", response_model=TicketSchema)
def add_message_to_ticket(
    ticket_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_in: TicketMessageCreate
):
    """
    Add a new message to an existing ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    new_message = TicketMessage(
        content=message_in.content,
        ticket_id=ticket.id,
        author_id=current_user.id
    )
    db.add(new_message)
    db.commit()
    db.refresh(ticket)
    return ticket