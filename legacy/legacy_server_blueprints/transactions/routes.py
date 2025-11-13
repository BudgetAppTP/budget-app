from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, timedelta
from .forms import IncomeForm, ExpenseForm
bp = Blueprint("transactions", __name__, url_prefix="/transactions")


demo_incomes = [
    {"id": 1, "date": "2025-10-01", "description": "Výplata", "amount": 1200.00},
    {"id": 2, "date": "2025-10-05", "description": "Darček od babky", "amount": 200.00},
    {"id": 3, "date": "2025-10-10", "description": "Predaj starého bicykla", "amount": 350.00},
]

demo_expenses = [
    {"id": 1, "date": "2025-10-02", "category": "Jedlo", "amount": 45.20},
    {"id": 2, "date": "2025-10-05", "category": "Doprava", "amount": 14.00},
    {"id": 3, "date": "2025-10-07", "category": "Byvanie", "amount": 865.00},
]

@bp.route("/incomes", methods=["GET", "POST"])
def income_list():
    form = IncomeForm()
    if form.validate_on_submit():
        new_income = {
            "id": demo_incomes[-1]["id"] + 1 if demo_incomes else 1,
            "date": form.date.data.strftime("%Y-%m-%d"),
            "description": form.description.data,
            "amount": float(form.amount.data),
        }
        demo_incomes.append(new_income)
        flash("Záznam pridaný!", "success")
        return redirect(url_for("transactions.income_list"))

    total_amount = sum(i["amount"] for i in demo_incomes)
    return render_template(
        "transactions/create_income.html",
        incomes=demo_incomes,
        total_amount=total_amount,
        form=form,
    )

@bp.post("/add")
def add_income():
    data = request.get_json()
    new_id = demo_incomes[-1]["id"] + 1 if demo_incomes else 1
    new_income = {
        "id": new_id,
        "date": data["date"],
        "description": data["description"],
        "amount": float(data["amount"]),
    }
    demo_incomes.append(new_income)
    return jsonify({"success": True, "incomes": demo_incomes})

@bp.delete("/delete/<int:item_id>")
def delete_income(item_id):
    global demo_incomes
    demo_incomes = [i for i in demo_incomes if i["id"] != item_id]
    return jsonify({"success": True, "incomes": demo_incomes})

@bp.put("/edit/<int:item_id>")
def edit_income(item_id):
    data = request.get_json()
    for i in demo_incomes:
        if i["id"] == item_id:
            i["date"] = data["date"]
            i["description"] = data["description"]
            i["amount"] = float(data["amount"])
    return jsonify({"success": True, "incomes": demo_incomes})


@bp.get("/sort")
def sort_incomes():
    field = request.args.get("field", "date")
    order = request.args.get("order", "asc")
    reverse = (order == "desc")
    sorted_incomes = sorted(
        demo_incomes,
        key=lambda x: float(x["amount"]) if field == "amount" else x["date"],
        reverse=reverse,
    )
    return jsonify({"success": True, "incomes": sorted_incomes})


@bp.route("/expenses", methods=["GET", "POST"])
def expense_list():
    form = ExpenseForm()
    categories = ["Jedlo", "Doprava", "Byvanie", "Voľný čas"]

    total_amount = sum(e["amount"] for e in demo_expenses)
    return render_template(
        "transactions/create_expense.html",
        expenses=demo_expenses,
        total_amount=total_amount,
        form=form,
        categories=categories,
    )

@bp.post("/expenses/add")
def add_expense():
    try:
        data = request.get_json(force=True)
        new_id = demo_expenses[-1]["id"] + 1 if demo_expenses else 1
        new_expense = {
            "id": new_id,
            "date": data.get("date", ""),
            "category": data.get("category", ""),
            "amount": float(data.get("amount", 0)),
        }
        demo_expenses.append(new_expense)
        print("Nový výdavok pridaný:", new_expense)
        return jsonify(new_expense), 200
    except Exception as e:
        print("Chyba pri ukladaní výdavku:", e)
        return jsonify({"error": str(e)}), 500


@bp.delete("/expenses/delete/<int:item_id>")
def delete_expense(item_id):
    demo_expenses = [e for e in demo_expenses if e["id"] != item_id]
    return jsonify({"success": True})

@bp.put("/expenses/edit/<int:item_id>")
def edit_expense(item_id):
    data = request.get_json(force=True)
    for e in demo_expenses:
        if e["id"] == item_id:
            e["date"] = data["date"]
            e["category"] = data["category"]
            e["amount"] = float(data["amount"])
    return jsonify({"success": True})


@bp.route("/new-expense")
def new_expense():
    return redirect(url_for("transactions.expense_list"))


    @bp.route("/budget", methods=["GET"])
    def monthly_budget():
        month_param = request.args.get("month")
        if month_param:
            try:
                selected_month = datetime.strptime(month_param, "%Y-%m")
            except ValueError:
                selected_month = datetime.now()
        else:
            selected_month = datetime.now()

        month_name = selected_month.strftime("%B %Y")
        current_month_key = selected_month.strftime("%Y-%m")

        demo_data = {
            "2025-10": {
                "incomes": [
                    {"id": 1, "date": "2025-10-01", "description": "Výplata", "amount": 1200.00},
                    {"id": 2, "date": "2025-10-10", "description": "Darček", "amount": 100.00},
                ],
                "expenses": [
                    {"id": 1, "date": "2025-10-03", "category": "Jedlo", "amount": 80.00},
                    {"id": 2, "date": "2025-10-07", "category": "Byvanie", "amount": 600.00},
                    {"id": 3, "date": "2025-10-10", "category": "Doprava", "amount": 50.00},
                ],
                "planning": [
                    {"category": "Potreby", "percent": 40, "amount": 800.00},
                    {"category": "Voľný čas", "percent": 10, "amount": 200.00},
                    {"category": "Sporenie", "percent": 40, "amount": 800.00},
                    {"category": "Investovanie", "percent": 10, "amount": 200.00},
                ],
            },
            "2025-11": {
                "incomes": [
                    {"id": 1, "date": "2025-11-01", "description": "Výplata", "amount": 1300.00},
                ],
                "expenses": [
                    {"id": 1, "date": "2025-11-05", "category": "Jedlo", "amount": 120.00},
                    {"id": 2, "date": "2025-11-09", "category": "Byvanie", "amount": 600.00},
                ],
                "planning": [
                    {"category": "Potreby", "percent": 40, "amount": 850.00},
                    {"category": "Voľný čas", "percent": 10, "amount": 210.00},
                    {"category": "Sporenie", "percent": 40, "amount": 850.00},
                    {"category": "Investovanie", "percent": 10, "amount": 210.00},
                ],
            },
        }


        month_data = demo_data.get(current_month_key, demo_data["2025-10"])
        incomes = month_data["incomes"]
        expenses = month_data["expenses"]
        planning = month_data["planning"]

        total_income = sum(i["amount"] for i in incomes)
        total_expense = sum(e["amount"] for e in expenses)
        balance = total_income - total_expense


        prev_month = (selected_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        next_month = (selected_month.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m")

        return render_template(
            "transactions/monthly_budget.html",
            month=month_name,
            month_key=current_month_key,
            incomes=incomes,
            expenses=expenses,
            planning=planning,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            prev_month=prev_month,
            next_month=next_month,
        )


@bp.route("/budget", methods=["GET"])
def monthly_budget():
    from datetime import datetime, timedelta

    month_param = request.args.get("month")
    if month_param:
        try:
            selected_month = datetime.strptime(month_param, "%Y-%m")
        except ValueError:
            selected_month = datetime.now()
    else:
        selected_month = datetime.now()

    month_name = selected_month.strftime("%B %Y").capitalize()
    current_month_key = selected_month.strftime("%Y-%m")

    demo_data = {
        "2025-01": {
            "incomes": [
                {"id": 1, "date": "2025-01-05", "description": "Výplata", "amount": 1000.00},
                {"id": 2, "date": "2025-01-12", "description": "Bonus", "amount": 200.00},
            ],
            "expenses": [
                {"id": 1, "date": "2025-01-08", "category": "Jedlo", "amount": 90.00},
                {"id": 2, "date": "2025-01-15", "category": "Byvanie", "amount": 700.00},
            ],
            "planning": [
                {"category": "Potreby", "percent": 40, "amount": 0},
                {"category": "Voľný čas", "percent": 10, "amount": 0},
                {"category": "Sporenie", "percent": 40, "amount": 0},
                {"category": "Investovanie", "percent": 10, "amount": 0},
            ],
        },
        "2025-10": {
            "incomes": [
                {"id": 1, "date": "2025-10-01", "description": "Výplata", "amount": 1200.00},
                {"id": 2, "date": "2025-10-10", "description": "Darček", "amount": 100.00},
                {"id": 3, "date": "2025-10-15", "description": "Predaj bicykla", "amount": 350.00},
            ],
            "expenses": [
                {"id": 1, "date": "2025-10-02", "category": "Jedlo", "amount": 45.20},
                {"id": 2, "date": "2025-10-07", "category": "Byvanie", "amount": 865.00},
            ],
            "planning": [
                {"category": "Potreby", "percent": 40, "amount": 0},
                {"category": "Voľný čas", "percent": 10, "amount": 0},
                {"category": "Sporenie", "percent": 40, "amount": 0},
                {"category": "Investovanie", "percent": 10, "amount": 0},
            ],
        },
        "2025-11": {
            "incomes": [
                {"id": 1, "date": "2025-11-01", "description": "Výplata", "amount": 1300.00},
            ],
            "expenses": [
                {"id": 1, "date": "2025-11-05", "category": "Jedlo", "amount": 120.00},
                {"id": 2, "date": "2025-11-09", "category": "Byvanie", "amount": 600.00},
            ],
            "planning": [
                {"category": "Potreby", "percent": 40, "amount": 0},
                {"category": "Voľný čas", "percent": 10, "amount": 0},
                {"category": "Sporenie", "percent": 40, "amount": 0},
                {"category": "Investovanie", "percent": 10, "amount": 0},
            ],
        },
    }

    month_data = demo_data.get(current_month_key, demo_data["2025-10"])
    incomes = month_data["incomes"]
    expenses = month_data["expenses"]
    planning = month_data["planning"]

    total_income = sum(i["amount"] for i in incomes)
    total_expense = sum(e["amount"] for e in expenses)
    balance = total_income - total_expense

    prev_month = (selected_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    next_month = (selected_month.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m")

    return render_template(
        "transactions/list.html",
        month=month_name,
        month_key=current_month_key,
        incomes=incomes,
        expenses=expenses,
        planning=planning,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        prev_month=prev_month,
        next_month=next_month,
    )
