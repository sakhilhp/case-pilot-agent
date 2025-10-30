"""
Credit History Analyzer Tool for mortgage processing.

This tool performs comprehensive credit history analysis including payment patterns,
utilization analysis, account management evaluation, behavioral insights, and public records review.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import statistics

from ..base import BaseTool, ToolResult


class CreditHistoryAnalyzerTool(BaseTool):
    """
    Tool for comprehensive credit history analysis for mortgage applications.
    
    This tool analyzes credit history to:
    - Evaluate payment patterns and consistency over time
    - Analyze credit utilization trends and management
    - Assess account management and credit mix
    - Provide behavioral insights and risk indicators
    - Review public records and derogatory marks
    - Generate detailed credit profile assessment
    """
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="credit_history_analyzer",
            description="Comprehensive credit history analysis with payment patterns, utilization, and behavioral insights",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            agent_domain="credit_assessment"
        )
        
        # Payment history scoring weights
        self.payment_weights = {
            "current": 1.0,
            "30_days": 0.8,
            "60_days": 0.6,
            "90_days": 0.4,
            "120_days": 0.2
        }
        
        # Utilization thresholds
        self.utilization_thresholds = {
            "excellent": 0.10,
            "good": 0.30,
            "fair": 0.50,
            "poor": 0.70,
            "very_poor": 1.0
        }
        
        # Account age scoring
        self.age_scoring = {
            "excellent": 120,  # 10+ years
            "good": 60,        # 5+ years
            "fair": 36,        # 3+ years
            "poor": 24,        # 2+ years
            "very_poor": 12    # 1+ year
        }
        
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "string",
                    "description": "Unique identifier for the mortgage application"
                },
                "borrower_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ssn": {"type": "string"},
                        "date_of_birth": {"type": "string"}
                    },
                    "required": ["name", "ssn"]
                },
                "credit_documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string"},
                            "document_type": {"type": "string"},
                            "extracted_data": {"type": "object"},
                            "file_path": {"type": "string"}
                        },
                        "required": ["document_id", "document_type", "extracted_data"]
                    }
                },
                "credit_score_info": {
                    "type": "object",
                    "properties": {
                        "credit_score": {"type": "number"},
                        "score_model": {"type": "string"},
                        "score_date": {"type": "string"}
                    }
                },
                "analysis_depth": {
                    "type": "string",
                    "enum": ["basic", "standard", "comprehensive"],
                    "description": "Depth of analysis to perform"
                }
            },
            "required": ["application_id", "borrower_info"]
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for credit history analysis."""
        return {
            "type": "object",
            "required": ["applicant_id", "credit_report"],
            "properties": {
                "applicant_id": {
                    "type": "string",
                    "description": "Unique identifier for the applicant"
                },
                "credit_report": {
                    "type": "object",
                    "description": "Credit report data with accounts and payment history",
                    "properties": {
                        "accounts": {"type": "array"},
                        "inquiries": {"type": "array"},
                        "public_records": {"type": "array"}
                    }
                }
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute comprehensive credit history analysis.
        
        Args:
            application_id: Unique identifier for the mortgage application
            borrower_info: Information about the borrower
            credit_documents: List of credit-related documents (optional)
            credit_score_info: Credit score information from previous analysis (optional)
            analysis_depth: Depth of analysis (basic, standard, comprehensive)
            
        Returns:
            ToolResult containing credit history analysis
        """
        try:
            application_id = kwargs["application_id"]
            borrower_info = kwargs["borrower_info"]
            credit_documents = kwargs.get("credit_documents", [])
            credit_score_info = kwargs.get("credit_score_info", {})
            analysis_depth = kwargs.get("analysis_depth", "standard")
            
            self.logger.info(f"Starting credit history analysis for application {application_id}")
            
            # Pull comprehensive credit history (simulate credit bureau data)
            credit_history = await self._pull_credit_history(borrower_info, credit_documents)
            
            # Analyze payment history patterns
            payment_analysis = self._analyze_payment_history(credit_history)
            
            # Analyze credit utilization patterns
            utilization_analysis = self._analyze_utilization_patterns(credit_history)
            
            # Analyze account management
            account_analysis = self._analyze_account_management(credit_history)
            
            # Analyze credit mix and diversity
            mix_analysis = self._analyze_credit_mix(credit_history)
            
            # Analyze temporal patterns and trends
            temporal_analysis = self._analyze_temporal_patterns(credit_history)
            
            # Review public records and derogatory marks
            public_records_analysis = self._analyze_public_records(credit_history)
            
            # Generate behavioral insights
            behavioral_insights = self._generate_behavioral_insights(
                payment_analysis, utilization_analysis, account_analysis, temporal_analysis
            )
            
            # Perform comprehensive analysis if requested
            if analysis_depth == "comprehensive":
                advanced_analysis = self._perform_advanced_analysis(credit_history)
            else:
                advanced_analysis = {}
            
            # Calculate overall credit history score
            history_score = self._calculate_history_score(
                payment_analysis, utilization_analysis, account_analysis, 
                mix_analysis, public_records_analysis
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                payment_analysis, utilization_analysis, account_analysis,
                public_records_analysis, behavioral_insights
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                credit_history, credit_documents, analysis_depth
            )
            
            result_data = {
                "payment_history_score": payment_analysis["overall_score"],
                "late_payments_12_months": payment_analysis["late_payments_12_months"],
                "late_payments_24_months": payment_analysis["late_payments_24_months"],
                "payment_consistency": payment_analysis["consistency_rating"],
                "credit_utilization_ratio": utilization_analysis["current_utilization"],
                "utilization_trend": utilization_analysis["trend"],
                "utilization_stability": utilization_analysis["stability"],
                "credit_age_months": account_analysis["average_age_months"],
                "oldest_account_months": account_analysis["oldest_account_months"],
                "account_mix_score": mix_analysis["diversity_score"],
                "total_accounts": account_analysis["total_accounts"],
                "open_accounts": account_analysis["open_accounts"],
                "closed_accounts": account_analysis["closed_accounts"],
                "bankruptcies": public_records_analysis["bankruptcies"],
                "foreclosures": public_records_analysis["foreclosures"],
                "collections": public_records_analysis["collections"],
                "charge_offs": public_records_analysis["charge_offs"],
                "recent_bankruptcy": public_records_analysis["recent_bankruptcy"],
                "pattern_of_late_payments": behavioral_insights["pattern_of_late_payments"],
                "credit_seeking_behavior": behavioral_insights["credit_seeking_behavior"],
                "financial_stress_indicators": behavioral_insights["stress_indicators"],
                "positive_trends": behavioral_insights["positive_trends"],
                "negative_trends": behavioral_insights["negative_trends"],
                "overall_history_score": history_score["total_score"],
                "history_grade": history_score["grade"],
                "confidence_score": confidence_score,
                "recommendations": recommendations,
                "suspicious_activity": self._detect_suspicious_activity(credit_history),
                "debt_analysis": self._analyze_debt_structure(credit_history),
                "risk_factors": self._identify_risk_factors(
                    payment_analysis, utilization_analysis, public_records_analysis
                )
            }
            
            # Add advanced analysis if performed
            if advanced_analysis:
                result_data.update(advanced_analysis)
            
            self.logger.info(f"Credit history analysis completed for application {application_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Credit history analysis failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _pull_credit_history(self, borrower_info: Dict[str, Any], 
                                 credit_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simulate pulling comprehensive credit history from credit bureau.
        
        In a real implementation, this would integrate with credit bureau APIs
        to get detailed credit history data.
        
        Args:
            borrower_info: Borrower information
            credit_documents: Available credit documents
            
        Returns:
            Dictionary containing comprehensive credit history
        """
        import random
        from datetime import datetime, timedelta
        
        # Generate consistent data based on borrower name
        name_hash = hash(borrower_info.get("name", "")) % 1000
        
        # Generate account history
        num_accounts = 5 + (name_hash % 15)  # 5-20 accounts
        accounts = []
        
        account_types = ["credit_card", "auto_loan", "mortgage", "student_loan", "personal_loan"]
        
        for i in range(num_accounts):
            account_age_months = random.randint(6, 180)
            is_open = random.choice([True, False]) if account_age_months > 24 else True
            
            # Generate payment history
            payment_history = []
            for month in range(min(24, account_age_months)):
                # Most payments are on time, with occasional lates
                if random.random() < 0.85:  # 85% on-time payments
                    payment_history.append("current")
                elif random.random() < 0.10:
                    payment_history.append("30_days")
                elif random.random() < 0.03:
                    payment_history.append("60_days")
                else:
                    payment_history.append("90_days")
            
            account = {
                "account_id": f"ACC_{i+1:03d}",
                "account_type": random.choice(account_types),
                "creditor": f"Creditor {i+1}",
                "opened_date": (datetime.now() - timedelta(days=account_age_months*30)).isoformat(),
                "closed_date": None if is_open else (datetime.now() - timedelta(days=random.randint(1, 12)*30)).isoformat(),
                "is_open": is_open,
                "credit_limit": random.randint(1000, 50000) if "credit_card" in account["account_type"] else None,
                "current_balance": random.randint(0, 25000),
                "monthly_payment": random.randint(50, 500),
                "payment_history": payment_history,
                "high_balance": random.randint(5000, 75000),
                "account_status": "open" if is_open else "closed"
            }
            accounts.append(account)
        
        # Generate public records
        public_records = {
            "bankruptcies": [],
            "foreclosures": [],
            "tax_liens": [],
            "judgments": []
        }
        
        # Occasionally add public records
        if random.random() < 0.15:  # 15% chance of bankruptcy
            bankruptcy_date = datetime.now() - timedelta(days=random.randint(365, 2555))  # 1-7 years ago
            public_records["bankruptcies"].append({
                "type": "Chapter 7",
                "filed_date": bankruptcy_date.isoformat(),
                "discharged_date": (bankruptcy_date + timedelta(days=120)).isoformat(),
                "status": "discharged"
            })
        
        if random.random() < 0.08:  # 8% chance of foreclosure
            foreclosure_date = datetime.now() - timedelta(days=random.randint(730, 2555))  # 2-7 years ago
            public_records["foreclosures"].append({
                "property_address": "123 Foreclosed St",
                "filed_date": foreclosure_date.isoformat(),
                "status": "completed"
            })
        
        # Generate collections
        collections = []
        num_collections = random.randint(0, 3) if random.random() < 0.25 else 0
        for i in range(num_collections):
            collection_date = datetime.now() - timedelta(days=random.randint(180, 1095))  # 6 months to 3 years
            collections.append({
                "creditor": f"Collection Agency {i+1}",
                "original_creditor": f"Original Creditor {i+1}",
                "amount": random.randint(200, 5000),
                "date_reported": collection_date.isoformat(),
                "status": random.choice(["unpaid", "paid", "settled"])
            })
        
        return {
            "accounts": accounts,
            "public_records": public_records,
            "collections": collections,
            "inquiries": self._generate_inquiries(),
            "summary": {
                "total_accounts": len(accounts),
                "open_accounts": sum(1 for acc in accounts if acc["is_open"]),
                "closed_accounts": sum(1 for acc in accounts if not acc["is_open"]),
                "total_balance": sum(acc["current_balance"] for acc in accounts),
                "total_credit_limit": sum(acc.get("credit_limit", 0) for acc in accounts if acc.get("credit_limit")),
                "oldest_account_date": min(acc["opened_date"] for acc in accounts) if accounts else None
            }
        }
    
    def _generate_inquiries(self) -> List[Dict[str, Any]]:
        """Generate credit inquiry history."""
        import random
        from datetime import datetime, timedelta
        
        inquiries = []
        num_inquiries = random.randint(0, 8)
        
        for i in range(num_inquiries):
            inquiry_date = datetime.now() - timedelta(days=random.randint(1, 730))  # Last 2 years
            inquiries.append({
                "creditor": f"Creditor Inquiry {i+1}",
                "inquiry_type": random.choice(["hard", "soft"]),
                "date": inquiry_date.isoformat(),
                "purpose": random.choice(["credit_card", "auto_loan", "mortgage", "personal_loan"])
            })
        
        return inquiries
    
    def _analyze_payment_history(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze payment history patterns across all accounts.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing payment history analysis
        """
        accounts = credit_history.get("accounts", [])
        
        if not accounts:
            return {
                "overall_score": 50,
                "late_payments_12_months": 0,
                "late_payments_24_months": 0,
                "consistency_rating": "insufficient_data",
                "payment_trends": [],
                "worst_delinquency": "current"
            }
        
        # Aggregate payment data
        total_payments = 0
        late_payments_12m = 0
        late_payments_24m = 0
        late_30_count = 0
        late_60_count = 0
        late_90_count = 0
        
        payment_scores = []
        
        for account in accounts:
            payment_history = account.get("payment_history", [])
            
            for i, payment in enumerate(payment_history):
                total_payments += 1
                
                # Count recent late payments
                if i < 12:  # Last 12 months
                    if payment != "current":
                        late_payments_12m += 1
                
                if i < 24:  # Last 24 months
                    if payment != "current":
                        late_payments_24m += 1
                
                # Count by severity
                if payment == "30_days":
                    late_30_count += 1
                elif payment == "60_days":
                    late_60_count += 1
                elif payment == "90_days":
                    late_90_count += 1
                
                # Calculate weighted score for this payment
                payment_scores.append(self.payment_weights.get(payment, 0))
        
        # Calculate overall payment score
        if payment_scores:
            overall_score = (sum(payment_scores) / len(payment_scores)) * 100
        else:
            overall_score = 50
        
        # Determine consistency rating
        if late_payments_12m == 0:
            consistency_rating = "excellent"
        elif late_payments_12m <= 2:
            consistency_rating = "good"
        elif late_payments_12m <= 4:
            consistency_rating = "fair"
        else:
            consistency_rating = "poor"
        
        # Determine worst delinquency
        if late_90_count > 0:
            worst_delinquency = "90_days"
        elif late_60_count > 0:
            worst_delinquency = "60_days"
        elif late_30_count > 0:
            worst_delinquency = "30_days"
        else:
            worst_delinquency = "current"
        
        # Analyze payment trends
        payment_trends = self._analyze_payment_trends(accounts)
        
        return {
            "overall_score": round(overall_score, 1),
            "late_payments_12_months": late_payments_12m,
            "late_payments_24_months": late_payments_24m,
            "late_30_count": late_30_count,
            "late_60_count": late_60_count,
            "late_90_count": late_90_count,
            "consistency_rating": consistency_rating,
            "payment_trends": payment_trends,
            "worst_delinquency": worst_delinquency,
            "total_payment_records": total_payments
        }
    
    def _analyze_payment_trends(self, accounts: List[Dict[str, Any]]) -> List[str]:
        """Analyze trends in payment behavior."""
        trends = []
        
        # Analyze recent vs. older payment patterns
        recent_lates = 0
        older_lates = 0
        
        for account in accounts:
            payment_history = account.get("payment_history", [])
            
            # Recent 6 months vs. 7-12 months ago
            for i, payment in enumerate(payment_history):
                if i < 6 and payment != "current":
                    recent_lates += 1
                elif 6 <= i < 12 and payment != "current":
                    older_lates += 1
        
        if recent_lates < older_lates:
            trends.append("improving_payment_behavior")
        elif recent_lates > older_lates:
            trends.append("deteriorating_payment_behavior")
        else:
            trends.append("stable_payment_behavior")
        
        return trends
    
    def _analyze_utilization_patterns(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze credit utilization patterns and trends.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing utilization analysis
        """
        accounts = credit_history.get("accounts", [])
        
        # Filter to revolving accounts (credit cards)
        revolving_accounts = [acc for acc in accounts 
                            if acc.get("account_type") == "credit_card" and acc.get("is_open")]
        
        if not revolving_accounts:
            return {
                "current_utilization": 0.0,
                "utilization_rating": "no_revolving_credit",
                "trend": "stable",
                "stability": "stable",
                "individual_utilizations": [],
                "high_utilization_accounts": 0
            }
        
        # Calculate current utilization
        total_balance = sum(acc.get("current_balance", 0) for acc in revolving_accounts)
        total_limit = sum(acc.get("credit_limit", 0) for acc in revolving_accounts)
        
        current_utilization = total_balance / total_limit if total_limit > 0 else 0
        
        # Calculate individual account utilizations
        individual_utilizations = []
        high_util_accounts = 0
        
        for account in revolving_accounts:
            balance = account.get("current_balance", 0)
            limit = account.get("credit_limit", 0)
            
            if limit > 0:
                util = balance / limit
                individual_utilizations.append({
                    "account_id": account.get("account_id"),
                    "utilization": util,
                    "balance": balance,
                    "limit": limit
                })
                
                if util > 0.70:  # High utilization threshold
                    high_util_accounts += 1
        
        # Determine utilization rating
        if current_utilization <= self.utilization_thresholds["excellent"]:
            utilization_rating = "excellent"
        elif current_utilization <= self.utilization_thresholds["good"]:
            utilization_rating = "good"
        elif current_utilization <= self.utilization_thresholds["fair"]:
            utilization_rating = "fair"
        elif current_utilization <= self.utilization_thresholds["poor"]:
            utilization_rating = "poor"
        else:
            utilization_rating = "very_poor"
        
        # Simulate trend analysis (in real implementation, would use historical data)
        import random
        trend = random.choice(["improving", "stable", "deteriorating"])
        stability = random.choice(["stable", "volatile"])
        
        return {
            "current_utilization": round(current_utilization, 3),
            "utilization_rating": utilization_rating,
            "trend": trend,
            "stability": stability,
            "individual_utilizations": individual_utilizations,
            "high_utilization_accounts": high_util_accounts,
            "total_revolving_balance": total_balance,
            "total_revolving_limit": total_limit,
            "revolving_accounts_count": len(revolving_accounts)
        }
    
    def _analyze_account_management(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze account management patterns and credit age.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing account management analysis
        """
        accounts = credit_history.get("accounts", [])
        
        if not accounts:
            return {
                "total_accounts": 0,
                "open_accounts": 0,
                "closed_accounts": 0,
                "average_age_months": 0,
                "oldest_account_months": 0,
                "newest_account_months": 0,
                "account_management_score": 50
            }
        
        # Calculate account ages
        from datetime import datetime
        current_date = datetime.now()
        account_ages = []
        
        for account in accounts:
            opened_date = datetime.fromisoformat(account["opened_date"].replace('Z', '+00:00'))
            age_months = (current_date - opened_date).days / 30.44  # Average days per month
            account_ages.append(age_months)
        
        # Calculate statistics
        total_accounts = len(accounts)
        open_accounts = sum(1 for acc in accounts if acc.get("is_open", True))
        closed_accounts = total_accounts - open_accounts
        average_age_months = statistics.mean(account_ages) if account_ages else 0
        oldest_account_months = max(account_ages) if account_ages else 0
        newest_account_months = min(account_ages) if account_ages else 0
        
        # Calculate account management score
        management_score = self._calculate_account_management_score(
            average_age_months, oldest_account_months, total_accounts, open_accounts
        )
        
        return {
            "total_accounts": total_accounts,
            "open_accounts": open_accounts,
            "closed_accounts": closed_accounts,
            "average_age_months": round(average_age_months, 1),
            "oldest_account_months": round(oldest_account_months, 1),
            "newest_account_months": round(newest_account_months, 1),
            "account_management_score": management_score,
            "account_age_rating": self._rate_account_age(average_age_months, oldest_account_months)
        }
    
    def _calculate_account_management_score(self, avg_age: float, oldest_age: float, 
                                         total_accounts: int, open_accounts: int) -> int:
        """Calculate account management score based on various factors."""
        score = 50  # Base score
        
        # Age factor
        if oldest_age >= self.age_scoring["excellent"]:
            score += 20
        elif oldest_age >= self.age_scoring["good"]:
            score += 15
        elif oldest_age >= self.age_scoring["fair"]:
            score += 10
        
        if avg_age >= self.age_scoring["good"]:
            score += 10
        elif avg_age >= self.age_scoring["fair"]:
            score += 5
        
        # Account diversity factor
        if total_accounts >= 10:
            score += 10
        elif total_accounts >= 5:
            score += 5
        elif total_accounts < 3:
            score -= 10
        
        # Account management factor
        if open_accounts > 0:
            open_ratio = open_accounts / total_accounts
            if 0.5 <= open_ratio <= 0.8:  # Good balance of open/closed
                score += 5
        
        return max(0, min(100, score))
    
    def _rate_account_age(self, avg_age: float, oldest_age: float) -> str:
        """Rate the account age profile."""
        if oldest_age >= self.age_scoring["excellent"] and avg_age >= self.age_scoring["good"]:
            return "excellent"
        elif oldest_age >= self.age_scoring["good"] and avg_age >= self.age_scoring["fair"]:
            return "good"
        elif oldest_age >= self.age_scoring["fair"]:
            return "fair"
        else:
            return "poor"
    
    def _analyze_credit_mix(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze credit mix and account diversity.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing credit mix analysis
        """
        accounts = credit_history.get("accounts", [])
        
        if not accounts:
            return {
                "diversity_score": 0,
                "account_types": {},
                "mix_rating": "no_accounts"
            }
        
        # Count account types
        account_types = {}
        for account in accounts:
            acc_type = account.get("account_type", "unknown")
            account_types[acc_type] = account_types.get(acc_type, 0) + 1
        
        # Calculate diversity score
        num_types = len(account_types)
        diversity_score = min(100, num_types * 20)  # Max 100 for 5+ types
        
        # Determine mix rating
        if num_types >= 4:
            mix_rating = "excellent"
        elif num_types >= 3:
            mix_rating = "good"
        elif num_types >= 2:
            mix_rating = "fair"
        else:
            mix_rating = "poor"
        
        return {
            "diversity_score": diversity_score,
            "account_types": account_types,
            "mix_rating": mix_rating,
            "unique_account_types": num_types
        }
    
    def _analyze_temporal_patterns(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in credit behavior.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing temporal analysis
        """
        accounts = credit_history.get("accounts", [])
        inquiries = credit_history.get("inquiries", [])
        
        # Analyze account opening patterns
        from datetime import datetime, timedelta
        current_date = datetime.now()
        
        # Count new accounts by time period
        new_accounts_6m = 0
        new_accounts_12m = 0
        new_accounts_24m = 0
        
        for account in accounts:
            opened_date = datetime.fromisoformat(account["opened_date"].replace('Z', '+00:00'))
            months_ago = (current_date - opened_date).days / 30.44
            
            if months_ago <= 6:
                new_accounts_6m += 1
            if months_ago <= 12:
                new_accounts_12m += 1
            if months_ago <= 24:
                new_accounts_24m += 1
        
        # Analyze inquiry patterns
        hard_inquiries_6m = 0
        hard_inquiries_12m = 0
        
        for inquiry in inquiries:
            if inquiry.get("inquiry_type") == "hard":
                inquiry_date = datetime.fromisoformat(inquiry["date"].replace('Z', '+00:00'))
                months_ago = (current_date - inquiry_date).days / 30.44
                
                if months_ago <= 6:
                    hard_inquiries_6m += 1
                if months_ago <= 12:
                    hard_inquiries_12m += 1
        
        return {
            "new_accounts_6_months": new_accounts_6m,
            "new_accounts_12_months": new_accounts_12m,
            "new_accounts_24_months": new_accounts_24m,
            "hard_inquiries_6_months": hard_inquiries_6m,
            "hard_inquiries_12_months": hard_inquiries_12m,
            "credit_seeking_pattern": self._classify_credit_seeking_pattern(
                new_accounts_6m, hard_inquiries_6m
            )
        }
    
    def _classify_credit_seeking_pattern(self, new_accounts: int, inquiries: int) -> str:
        """Classify credit seeking behavior pattern."""
        if new_accounts >= 3 or inquiries >= 6:
            return "aggressive"
        elif new_accounts >= 2 or inquiries >= 4:
            return "moderate"
        elif new_accounts >= 1 or inquiries >= 2:
            return "conservative"
        else:
            return "minimal"
    
    def _analyze_public_records(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze public records and derogatory marks.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing public records analysis
        """
        public_records = credit_history.get("public_records", {})
        collections = credit_history.get("collections", [])
        
        # Count different types of public records
        bankruptcies = len(public_records.get("bankruptcies", []))
        foreclosures = len(public_records.get("foreclosures", []))
        tax_liens = len(public_records.get("tax_liens", []))
        judgments = len(public_records.get("judgments", []))
        collections_count = len(collections)
        
        # Check for recent bankruptcy (within 2 years)
        recent_bankruptcy = False
        if public_records.get("bankruptcies"):
            from datetime import datetime, timedelta
            current_date = datetime.now()
            
            for bankruptcy in public_records["bankruptcies"]:
                filed_date = datetime.fromisoformat(bankruptcy["filed_date"].replace('Z', '+00:00'))
                if (current_date - filed_date).days <= 730:  # 2 years
                    recent_bankruptcy = True
                    break
        
        # Calculate charge-offs from accounts
        charge_offs = 0
        for account in credit_history.get("accounts", []):
            if account.get("account_status") == "charge_off":
                charge_offs += 1
        
        return {
            "bankruptcies": bankruptcies,
            "foreclosures": foreclosures,
            "tax_liens": tax_liens,
            "judgments": judgments,
            "collections": collections_count,
            "charge_offs": charge_offs,
            "recent_bankruptcy": recent_bankruptcy,
            "total_derogatory_marks": bankruptcies + foreclosures + tax_liens + judgments + collections_count + charge_offs,
            "public_records_impact": self._assess_public_records_impact(
                bankruptcies, foreclosures, collections_count, recent_bankruptcy
            )
        }
    
    def _assess_public_records_impact(self, bankruptcies: int, foreclosures: int, 
                                    collections: int, recent_bankruptcy: bool) -> str:
        """Assess the impact level of public records."""
        if recent_bankruptcy or bankruptcies > 1 or foreclosures > 0:
            return "severe"
        elif bankruptcies > 0 or collections > 2:
            return "moderate"
        elif collections > 0:
            return "minor"
        else:
            return "none"
    
    def _generate_behavioral_insights(self, payment_analysis: Dict[str, Any],
                                    utilization_analysis: Dict[str, Any],
                                    account_analysis: Dict[str, Any],
                                    temporal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate behavioral insights from credit patterns.
        
        Args:
            payment_analysis: Payment history analysis
            utilization_analysis: Utilization analysis
            account_analysis: Account management analysis
            temporal_analysis: Temporal patterns analysis
            
        Returns:
            Dictionary containing behavioral insights
        """
        insights = {
            "pattern_of_late_payments": False,
            "credit_seeking_behavior": "normal",
            "stress_indicators": [],
            "positive_trends": [],
            "negative_trends": [],
            "financial_discipline": "moderate"
        }
        
        # Analyze payment patterns
        if payment_analysis["late_payments_12_months"] >= 3:
            insights["pattern_of_late_payments"] = True
            insights["negative_trends"].append("Consistent late payment pattern")
        elif payment_analysis["consistency_rating"] == "excellent":
            insights["positive_trends"].append("Excellent payment consistency")
        
        # Analyze credit seeking behavior
        seeking_pattern = temporal_analysis.get("credit_seeking_pattern", "minimal")
        insights["credit_seeking_behavior"] = seeking_pattern
        
        if seeking_pattern == "aggressive":
            insights["stress_indicators"].append("Aggressive credit seeking behavior")
            insights["negative_trends"].append("High credit application activity")
        
        # Analyze utilization behavior
        utilization = utilization_analysis.get("current_utilization", 0)
        if utilization > 0.70:
            insights["stress_indicators"].append("Very high credit utilization")
            insights["negative_trends"].append("Poor credit utilization management")
        elif utilization < 0.10:
            insights["positive_trends"].append("Excellent credit utilization management")
        
        # Analyze account management
        if account_analysis.get("account_age_rating") == "excellent":
            insights["positive_trends"].append("Long-established credit history")
        
        # Determine financial discipline
        positive_count = len(insights["positive_trends"])
        negative_count = len(insights["negative_trends"]) + len(insights["stress_indicators"])
        
        if positive_count > negative_count + 1:
            insights["financial_discipline"] = "excellent"
        elif positive_count > negative_count:
            insights["financial_discipline"] = "good"
        elif negative_count > positive_count + 1:
            insights["financial_discipline"] = "poor"
        else:
            insights["financial_discipline"] = "moderate"
        
        return insights
    
    def _perform_advanced_analysis(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform advanced analysis for comprehensive depth.
        
        Args:
            credit_history: Complete credit history data
            
        Returns:
            Dictionary containing advanced analysis results
        """
        return {
            "velocity_analysis": self._analyze_credit_velocity(credit_history),
            "seasonal_patterns": self._analyze_seasonal_patterns(credit_history),
            "risk_trajectory": self._analyze_risk_trajectory(credit_history),
            "peer_comparison": self._generate_peer_comparison(credit_history)
        }
    
    def _analyze_credit_velocity(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the velocity of credit changes."""
        # Simplified velocity analysis
        accounts = credit_history.get("accounts", [])
        recent_changes = sum(1 for acc in accounts 
                           if self._is_recent_account(acc.get("opened_date", "")))
        
        return {
            "recent_account_velocity": recent_changes,
            "velocity_rating": "high" if recent_changes >= 3 else "normal"
        }
    
    def _is_recent_account(self, opened_date: str) -> bool:
        """Check if account was opened recently (within 6 months)."""
        try:
            from datetime import datetime, timedelta
            opened = datetime.fromisoformat(opened_date.replace('Z', '+00:00'))
            return (datetime.now() - opened).days <= 180
        except:
            return False
    
    def _analyze_seasonal_patterns(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze seasonal credit behavior patterns."""
        # Placeholder for seasonal analysis
        return {
            "seasonal_utilization_changes": "stable",
            "holiday_spending_pattern": "moderate"
        }
    
    def _analyze_risk_trajectory(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk trajectory over time."""
        # Simplified risk trajectory
        return {
            "trajectory": "stable",
            "risk_direction": "neutral",
            "projected_risk_6_months": "stable"
        }
    
    def _generate_peer_comparison(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison to peer group."""
        # Simplified peer comparison
        return {
            "percentile_payment_history": 75,
            "percentile_utilization": 60,
            "percentile_credit_age": 80
        }
    
    def _calculate_history_score(self, payment_analysis: Dict[str, Any],
                               utilization_analysis: Dict[str, Any],
                               account_analysis: Dict[str, Any],
                               mix_analysis: Dict[str, Any],
                               public_records_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall credit history score.
        
        Args:
            payment_analysis: Payment history analysis
            utilization_analysis: Utilization analysis
            account_analysis: Account management analysis
            mix_analysis: Credit mix analysis
            public_records_analysis: Public records analysis
            
        Returns:
            Dictionary containing overall score and grade
        """
        # Weight factors (total = 100%)
        weights = {
            "payment_history": 0.35,
            "utilization": 0.30,
            "account_management": 0.15,
            "credit_mix": 0.10,
            "public_records": 0.10
        }
        
        # Component scores
        payment_score = payment_analysis.get("overall_score", 50)
        
        # Convert utilization rating to score
        util_rating = utilization_analysis.get("utilization_rating", "fair")
        util_scores = {"excellent": 100, "good": 80, "fair": 60, "poor": 40, "very_poor": 20}
        utilization_score = util_scores.get(util_rating, 50)
        
        account_score = account_analysis.get("account_management_score", 50)
        mix_score = mix_analysis.get("diversity_score", 50)
        
        # Public records penalty
        derogatory_count = public_records_analysis.get("total_derogatory_marks", 0)
        public_records_score = max(0, 100 - (derogatory_count * 20))
        
        # Calculate weighted total
        total_score = (
            payment_score * weights["payment_history"] +
            utilization_score * weights["utilization"] +
            account_score * weights["account_management"] +
            mix_score * weights["credit_mix"] +
            public_records_score * weights["public_records"]
        )
        
        # Determine grade
        if total_score >= 90:
            grade = "A+"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        elif total_score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "component_scores": {
                "payment_history": payment_score,
                "utilization": utilization_score,
                "account_management": account_score,
                "credit_mix": mix_score,
                "public_records": public_records_score
            }
        }
    
    def _generate_recommendations(self, payment_analysis: Dict[str, Any],
                                utilization_analysis: Dict[str, Any],
                                account_analysis: Dict[str, Any],
                                public_records_analysis: Dict[str, Any],
                                behavioral_insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on credit history analysis."""
        recommendations = []
        
        # Payment history recommendations
        if payment_analysis.get("late_payments_12_months", 0) > 0:
            recommendations.append("Obtain letter of explanation for recent late payments")
        
        if payment_analysis.get("consistency_rating") == "poor":
            recommendations.append("Consider payment history as significant risk factor")
        
        # Utilization recommendations
        utilization = utilization_analysis.get("current_utilization", 0)
        if utilization > 0.50:
            recommendations.append("Recommend borrower pay down credit card balances before closing")
        elif utilization > 0.30:
            recommendations.append("Consider credit utilization in risk assessment")
        
        # Account management recommendations
        if account_analysis.get("account_age_rating") == "poor":
            recommendations.append("Limited credit history - consider alternative credit data")
        
        # Public records recommendations
        if public_records_analysis.get("recent_bankruptcy"):
            recommendations.append("Recent bankruptcy requires manual underwriting review")
        
        if public_records_analysis.get("collections", 0) > 0:
            recommendations.append("Verify collection accounts are resolved or in payment plan")
        
        # Behavioral recommendations
        if behavioral_insights.get("pattern_of_late_payments"):
            recommendations.append("Pattern of late payments indicates payment management issues")
        
        if behavioral_insights.get("credit_seeking_behavior") == "aggressive":
            recommendations.append("Investigate reason for high recent credit activity")
        
        return recommendations
    
    def _calculate_confidence_score(self, credit_history: Dict[str, Any],
                                  credit_documents: List[Dict[str, Any]],
                                  analysis_depth: str) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.7
        
        # Adjust for data completeness
        accounts = credit_history.get("accounts", [])
        if len(accounts) >= 5:
            base_confidence += 0.1
        elif len(accounts) < 3:
            base_confidence -= 0.2
        
        # Adjust for document availability
        if credit_documents:
            base_confidence += 0.1
        
        # Adjust for analysis depth
        if analysis_depth == "comprehensive":
            base_confidence += 0.1
        elif analysis_depth == "basic":
            base_confidence -= 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _detect_suspicious_activity(self, credit_history: Dict[str, Any]) -> List[str]:
        """Detect suspicious activity patterns."""
        suspicious = []
        
        accounts = credit_history.get("accounts", [])
        
        # Check for rapid account opening
        recent_accounts = sum(1 for acc in accounts 
                            if self._is_recent_account(acc.get("opened_date", "")))
        if recent_accounts >= 4:
            suspicious.append("Rapid account opening pattern")
        
        # Check for inconsistent payment patterns
        # (This would be more sophisticated in a real implementation)
        
        return suspicious
    
    def _analyze_debt_structure(self, credit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze debt structure and composition."""
        accounts = credit_history.get("accounts", [])
        
        debt_by_type = {}
        total_debt = 0
        
        for account in accounts:
            acc_type = account.get("account_type", "unknown")
            balance = account.get("current_balance", 0)
            
            debt_by_type[acc_type] = debt_by_type.get(acc_type, 0) + balance
            total_debt += balance
        
        return {
            "total_debt": total_debt,
            "debt_by_type": debt_by_type,
            "revolving_debt_percentage": debt_by_type.get("credit_card", 0) / total_debt if total_debt > 0 else 0,
            "installment_debt_percentage": (debt_by_type.get("auto_loan", 0) + 
                                          debt_by_type.get("student_loan", 0) + 
                                          debt_by_type.get("personal_loan", 0)) / total_debt if total_debt > 0 else 0
        }
    
    def _identify_risk_factors(self, payment_analysis: Dict[str, Any],
                             utilization_analysis: Dict[str, Any],
                             public_records_analysis: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors from credit history."""
        risk_factors = []
        
        # Payment risk factors
        if payment_analysis.get("late_payments_12_months", 0) >= 3:
            risk_factors.append("Multiple recent late payments")
        
        if payment_analysis.get("worst_delinquency") in ["60_days", "90_days"]:
            risk_factors.append("Severe payment delinquencies")
        
        # Utilization risk factors
        if utilization_analysis.get("current_utilization", 0) > 0.80:
            risk_factors.append("Very high credit utilization")
        
        if utilization_analysis.get("high_utilization_accounts", 0) > 2:
            risk_factors.append("Multiple maxed-out credit accounts")
        
        # Public records risk factors
        if public_records_analysis.get("recent_bankruptcy"):
            risk_factors.append("Recent bankruptcy filing")
        
        if public_records_analysis.get("collections", 0) > 1:
            risk_factors.append("Multiple collection accounts")
        
        return risk_factors