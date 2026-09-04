"""Comprehensive Tests for Feature R1: Scholarship & Financial Aid Offer Comparison."""
import pytest
from server.models.portfolio import FinancialAidOffer
from server.services.aid_service import calculate_loan_payment
from tests.conftest import APIClient, SEED_COLLEGES


def test_financial_aid_offer_total_grants():
    """Verify total_grants sums merit, need, institutional, outside scholarships and excludes loans/work-study."""
    offer = FinancialAidOffer(
        merit_aid=5000,
        need_based_grants=10000,
        institutional_grants=8000,
        outside_scholarships=2000,
        federal_loans=5500,
        work_study=3000,
    )
    assert offer.total_grants == 25000
    assert offer.total_loans == 5500
    assert offer.total_self_help == 8500


def test_loan_amortization_calculation():
    """Verify 10-year standard loan repayment amortization formula at 5.5% APR."""
    # Zero loan debt
    assert calculate_loan_payment(0) == 0.0
    assert calculate_loan_payment(-100) == 0.0

    # $20,000 borrowed at 5.5% over 120 months
    # Formula: 20000 * (0.055/12 * (1 + 0.055/12)^120) / ((1 + 0.055/12)^120 - 1) = $217.05
    payment = calculate_loan_payment(20000, apr=0.055, n_months=120)
    assert 216.0 <= payment <= 218.0
    assert payment == 217.05


def test_financial_aid_metrics_calculation():
    """Verify net annual cost, 4-year total cost, and custom sticker price override."""
    offer = FinancialAidOffer(
        merit_aid=10000,
        need_based_grants=5000,
        federal_loans=5000,
        custom_sticker_price=40000,
    )
    metrics = offer.calculate_metrics(default_sticker_price=30000)
    assert metrics["sticker_price"] == 40000
    assert metrics["total_grants"] == 15000
    assert metrics["net_annual_cost"] == 25000
    assert metrics["four_year_total_cost"] == 100000
    assert metrics["total_debt_at_graduation"] == 20000
    assert metrics["estimated_monthly_payment"] == 217.05


def test_grants_exceeding_sticker_price_clamps_to_zero():
    """Edge case: When grants exceed sticker price, net annual cost clamps to 0."""
    offer = FinancialAidOffer(
        merit_aid=35000,
        need_based_grants=20000,
        custom_sticker_price=45000,
    )
    metrics = offer.calculate_metrics()
    assert metrics["total_grants"] == 55000
    assert metrics["net_annual_cost"] == 0
    assert metrics["four_year_total_cost"] == 0


def test_aid_service_comparison_and_best_value():
    """Verify aid_service determines best value school among saved colleges."""
    client = APIClient()
    c1_id = SEED_COLLEGES["mit"]["id"]
    c2_id = SEED_COLLEGES["stanford"]["id"]

    client.post("/api/portfolio/colleges", json={"college_id": c1_id})
    client.post("/api/portfolio/colleges", json={"college_id": c2_id})

    # Add generous offer to Stanford ($50,000 grants)
    res_aid1 = client.post(
        f"/api/portfolio/aid/{c2_id}",
        json={
            "merit_aid": 30000,
            "need_based_grants": 20000,
            "federal_loans": 2000,
            "custom_sticker_price": 60000,
        },
    )
    assert res_aid1.status_code == 200

    # Add modest offer to MIT ($10,000 grants)
    res_aid2 = client.post(
        f"/api/portfolio/aid/{c1_id}",
        json={
            "merit_aid": 10000,
            "federal_loans": 5000,
            "custom_sticker_price": 60000,
        },
    )
    assert res_aid2.status_code == 200

    # Get comparison payload
    comp_res = client.get("/api/portfolio/aid/comparison")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    assert comp_data["count_with_offers"] == 2
    assert comp_data["best_value_college_id"] == c2_id

    schools = comp_data["colleges"]
    stanford_item = next(s for s in schools if s["college_id"] == c2_id)
    mit_item = next(s for s in schools if s["college_id"] == c1_id)

    assert stanford_item["is_best_value"] is True
    assert stanford_item["net_annual_cost"] == 10000
    assert stanford_item["four_year_total_cost"] == 40000
    assert mit_item["is_best_value"] is False
    assert mit_item["net_annual_cost"] == 50000


def test_aid_offer_delete_lifecycle():
    """Verify deleting aid offer removes it from portfolio comparison."""
    client = APIClient()
    cid = SEED_COLLEGES["berkeley"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    # Save offer
    client.post(
        f"/api/portfolio/aid/{cid}",
        json={"merit_aid": 12000, "federal_loans": 3500},
    )
    comp_before = client.get("/api/portfolio/aid/comparison").json()
    assert comp_before["count_with_offers"] == 1

    # Delete offer
    del_res = client.delete(f"/api/portfolio/aid/{cid}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    comp_after = client.get("/api/portfolio/aid/comparison").json()
    assert comp_after["count_with_offers"] == 0


def test_financial_aid_loan_aliases_and_out_of_pocket():
    """Verify yearly loan aliases (yearly_loan, annual_loans) sync and out-of-pocket metrics are calculated."""
    offer = FinancialAidOffer(
        custom_sticker_price=50000,
        merit_aid=20000,
        yearly_loan=5000,
        work_study=2000,
    )
    assert offer.federal_loans == 5000
    metrics = offer.calculate_metrics()
    assert metrics["net_annual_cost"] == 30000
    assert metrics["annual_out_of_pocket"] == 23000  # 30000 - 5000 - 2000
    assert metrics["four_year_out_of_pocket"] == 92000
    assert metrics["total_debt_at_graduation"] == 20000
    assert metrics["estimated_monthly_payment"] == 217.05
