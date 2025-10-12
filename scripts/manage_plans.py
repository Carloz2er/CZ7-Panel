import argparse
import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.subscription import Plan

def create_plan(args):
    db = SessionLocal()
    new_plan = Plan(
        name=args.name,
        price=args.price,
        stripe_price_id=args.stripe_price_id,
        ram_mb=args.ram_mb,
        cpu_vcore=args.cpu_vcore,
        disk_gb=args.disk_gb,
        max_services=args.max_services
    )
    db.add(new_plan)
    db.commit()
    print(f"Plan '{args.name}' created successfully.")
    db.close()

def list_plans(args):
    db = SessionLocal()
    plans = db.query(Plan).all()
    if not plans:
        print("No plans found.")
    else:
        for plan in plans:
            print(f"ID: {plan.id}, Name: {plan.name}, Price: {plan.price}, RAM: {plan.ram_mb}MB, "
                  f"vCore: {plan.cpu_vcore}, Disk: {plan.disk_gb}GB, Max Services: {plan.max_services}, "
                  f"Stripe ID: {plan.stripe_price_id}")
    db.close()

def main():
    parser = argparse.ArgumentParser(description="Manage hosting plans.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    parser_create = subparsers.add_parser("create", help="Create a new plan.")
    parser_create.add_argument("--name", required=True, help="Name of the plan.")
    parser_create.add_argument("--price", type=float, required=True, help="Price of the plan.")
    parser_create.add_argument("--stripe-price-id", required=True, help="Stripe Price ID.")
    parser_create.add_argument("--ram-mb", type=int, required=True, help="RAM in MB.")
    parser_create.add_argument("--cpu-vcore", type=float, required=True, help="CPU vCore share.")
    parser_create.add_argument("--disk-gb", type=int, required=True, help="Disk space in GB.")
    parser_create.add_argument("--max-services", type=int, required=True, help="Maximum number of services.")
    parser_create.set_defaults(func=create_plan)

    # List command
    parser_list = subparsers.add_parser("list", help="List all plans.")
    parser_list.set_defaults(func=list_plans)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()