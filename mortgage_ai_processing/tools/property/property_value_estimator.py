"""Property Value Estimator Tool - Converted from TypeScript.

Automated Property Valuation for Mortgage Lending with multiple valuation approaches,
AVM integration, and comprehensive market analysis.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math

from ..base import BaseTool, ToolResult, ToolMetadata


class PropertyType(Enum):
    """Supported property types."""
    SINGLE_FAMILY_DETACHED = "single_family_detached"
    SINGLE_FAMILY_ATTACHED = "single_family_attached"
    CONDOMINIUM = "condominium"
    TOWNHOUSE = "townhouse"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    FOURPLEX = "fourplex"
    MANUFACTURED_HOME = "manufactured_home"
    COOPERATIVE = "cooperative"
    MULTIFAMILY_5PLUS = "multifamily_5plus"
    VACANT_LAND = "vacant_land"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"


class ValuationApproach(Enum):
    """Valuation approaches."""
    SALES_COMPARISON = "sales_comparison"
    COST_APPROACH = "cost_approach"
    INCOME_APPROACH = "income_approach"
    AUTOMATED_VALUATION_MODEL = "automated_valuation_model"
    BROKER_PRICE_OPINION = "broker_price_opinion"
    DESKTOP_APPRAISAL = "desktop_appraisal"
    DRIVE_BY_APPRAISAL = "drive_by_appraisal"
    FULL_APPRAISAL = "full_appraisal"


class PropertyCondition(Enum):
    """Property condition ratings."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    FAIR = "fair"
    POOR = "poor"
    NEEDS_RENOVATION = "needs_renovation"
    UNINHABITABLE = "uninhabitable"


class MarketCondition(Enum):
    """Market conditions."""
    SELLERS_MARKET = "sellers_market"
    BUYERS_MARKET = "buyers_market"
    BALANCED_MARKET = "balanced_market"


class PriceTrend(Enum):
    """Price trends."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class MarketPosition(Enum):
    """Market position."""
    BELOW_MARKET = "below_market"
    AT_MARKET = "at_market"
    ABOVE_MARKET = "above_market"


@dataclass
class PropertyDetails:
    """Property details structure."""
    address: str
    city: str
    state: str
    zip_code: str
    county: Optional[str] = None
    property_type: str = PropertyType.SINGLE_FAMILY_DETACHED.value
    year_built: int = 2000
    living_area_sqft: int = 2000
    lot_size_sqft: Optional[int] = None
    lot_size_acres: Optional[float] = None
    bedrooms: int = 3
    bathrooms: float = 2.0
    half_baths: Optional[int] = None
    garage_spaces: Optional[int] = None
    parking_type: Optional[str] = None
    basement: Optional[bool] = None
    basement_finished_sqft: Optional[int] = None
    stories: int = 1
    exterior_construction: Optional[str] = None
    roof_type: Optional[str] = None
    heating_type: Optional[str] = None
    cooling_type: Optional[str] = None
    fireplace_count: Optional[int] = None
    pool: Optional[bool] = None
    property_condition: str = PropertyCondition.GOOD.value
    renovation_date: Optional[str] = None
    zoning: Optional[str] = None
    flood_zone: Optional[str] = None
    hoa_fees: Optional[float] = None
    tax_assessment_value: Optional[float] = None
    annual_property_taxes: Optional[float] = None


@dataclass
class AdjustmentFactors:
    """Adjustment factors for comparable sales."""
    time_adjustment: float = 0.0
    size_adjustment: float = 0.0
    condition_adjustment: float = 0.0
    location_adjustment: float = 0.0
    feature_adjustments: float = 0.0
    total_adjustment: float = 0.0


@dataclass
class ComparableSale:
    """Comparable sale data structure."""
    address: str
    distance_miles: float
    sale_date: str
    sale_price: float
    living_area_sqft: int
    price_per_sqft: float
    bedrooms: int
    bathrooms: float
    lot_size_sqft: Optional[int] = None
    year_built: int = 2000
    property_condition: str = PropertyCondition.GOOD.value
    days_on_market: Optional[int] = None
    adjustment_factors: Optional[AdjustmentFactors] = None
    adjusted_price: float = 0.0
    weight_factor: float = 1.0


@dataclass
class MarketAnalysis:
    """Market analysis data structure."""
    market_conditions: str = MarketCondition.BALANCED_MARKET.value
    median_home_value: float = 400000.0
    median_price_per_sqft: float = 200.0
    year_over_year_appreciation: float = 3.0
    months_of_inventory: float = 4.0
    average_days_on_market: int = 30
    price_trend_6_months: str = PriceTrend.STABLE.value
    price_trend_12_months: str = PriceTrend.INCREASING.value
    seasonal_adjustment_factor: float = 1.0
    neighborhood_desirability_score: float = 7.0
    school_district_rating: Optional[float] = None
    walkability_score: Optional[int] = None
    crime_index: Optional[int] = None


@dataclass
class AVMResult:
    """AVM result data structure."""
    avm_provider: str
    estimated_value: float
    confidence_score: float
    value_range: Dict[str, float]
    forecast_change_12_months: Optional[float] = None
    data_quality_score: float = 80.0
    comparable_sales_count: int = 5
    last_updated: str = ""


@dataclass
class ValuationQuality:
    """Valuation quality metrics."""
    data_quality_score: float = 80.0
    comparable_quality_score: float = 80.0
    market_data_recency_score: float = 80.0
    methodology_reliability_score: float = 80.0
    overall_confidence: float = 80.0


@dataclass
class PropertyInsights:
    """Property insights and recommendations."""
    value_drivers: List[str]
    value_detractors: List[str]
    improvement_recommendations: List[str]
    market_position: str = MarketPosition.AT_MARKET.value


class PropertyValueEstimatorTool(BaseTool):
    """Tool for comprehensive property valuation using multiple approaches."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="property_value_estimator",
            description="Estimate property value using automated valuation models (AVM), comparable sales analysis, and multiple valuation approaches for mortgage lending decisions",
            version="1.0.0",
            author="Mortgage AI Processing System",
            tags=["property", "valuation", "avm", "appraisal", "mortgage", "real_estate"]
        )
        super().__init__(metadata)
        
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "property_details": {
                    "type": "object",
                    "description": "Detailed property information",
                    "properties": {
                        "address": {"type": "string", "description": "Property street address"},
                        "city": {"type": "string", "description": "City"},
                        "state": {"type": "string", "description": "State abbreviation"},
                        "zip_code": {"type": "string", "description": "ZIP code"},
                        "county": {"type": "string", "description": "County name"},
                        "property_type": {
                            "type": "string",
                            "enum": [pt.value for pt in PropertyType],
                            "description": "Type of property"
                        },
                        "year_built": {"type": "integer", "description": "Year property was built"},
                        "living_area_sqft": {"type": "integer", "description": "Living area in square feet"},
                        "lot_size_sqft": {"type": "integer", "description": "Lot size in square feet"},
                        "bedrooms": {"type": "integer", "description": "Number of bedrooms"},
                        "bathrooms": {"type": "number", "description": "Number of bathrooms"},
                        "garage_spaces": {"type": "integer", "description": "Number of garage spaces"},
                        "property_condition": {
                            "type": "string",
                            "enum": [pc.value for pc in PropertyCondition],
                            "description": "Overall property condition"
                        },
                        "pool": {"type": "boolean", "description": "Has swimming pool"},
                        "fireplace_count": {"type": "integer", "description": "Number of fireplaces"},
                        "basement": {"type": "boolean", "description": "Has basement"},
                        "basement_finished_sqft": {"type": "integer", "description": "Finished basement square feet"},
                        "hoa_fees": {"type": "number", "description": "Monthly HOA fees"},
                        "annual_property_taxes": {"type": "number", "description": "Annual property taxes"}
                    },
                    "required": ["address", "city", "state", "zip_code", "property_type", "year_built", "living_area_sqft", "bedrooms", "bathrooms"]
                },
                "valuation_approaches": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [va.value for va in ValuationApproach]
                    },
                    "description": "Valuation methodologies to use",
                    "default": ["sales_comparison", "automated_valuation_model"]
                },
                "purpose": {
                    "type": "string",
                    "enum": ["purchase", "refinance", "home_equity", "insurance", "tax_assessment", "investment"],
                    "description": "Purpose of the valuation",
                    "default": "purchase"
                },
                "appraisal_document_url": {
                    "type": "string",
                    "description": "URL to Form 1004 or other appraisal document"
                },
                "comparable_sales_radius_miles": {
                    "type": "number",
                    "description": "Search radius for comparable sales",
                    "default": 1.0,
                    "minimum": 0.1,
                    "maximum": 5.0
                },
                "comparable_sales_timeframe_months": {
                    "type": "integer",
                    "description": "Timeframe for comparable sales in months",
                    "default": 6,
                    "minimum": 1,
                    "maximum": 12
                },
                "minimum_comparable_sales": {
                    "type": "integer",
                    "description": "Minimum number of comparable sales required",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                },
                "use_external_avm_apis": {
                    "type": "boolean",
                    "description": "Whether to use external AVM APIs",
                    "default": True
                },
                "avm_providers": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["zillow", "attom", "corelogic", "realtytrac"]
                    },
                    "description": "External AVM providers to use",
                    "default": ["zillow", "attom"]
                },
                "market_analysis_required": {
                    "type": "boolean",
                    "description": "Whether to perform market analysis",
                    "default": True
                },
                "confidence_threshold": {
                    "type": "number",
                    "description": "Minimum confidence threshold to report estimate",
                    "default": 60.0,
                    "minimum": 0.0,
                    "maximum": 100.0
                },
                "mortgage_compliance_check": {
                    "type": "boolean",
                    "description": "FNMA/FHLMC compliance verification",
                    "default": True
                }
            },
            "required": ["property_details", "valuation_approaches", "purpose"],
            "additionalProperties": False
        }
        
    async def _execute(self, **kwargs) -> ToolResult:
        """Execute property valuation."""
        try:
            property_details_dict = kwargs.get("property_details", {})
            valuation_approaches = kwargs.get("valuation_approaches", ["sales_comparison", "automated_valuation_model"])
            purpose = kwargs.get("purpose", "purchase")
            appraisal_document_url = kwargs.get("appraisal_document_url")
            comparable_sales_radius_miles = kwargs.get("comparable_sales_radius_miles", 1.0)
            comparable_sales_timeframe_months = kwargs.get("comparable_sales_timeframe_months", 6)
            minimum_comparable_sales = kwargs.get("minimum_comparable_sales", 3)
            use_external_avm_apis = kwargs.get("use_external_avm_apis", True)
            avm_providers = kwargs.get("avm_providers", ["zillow", "attom"])
            market_analysis_required = kwargs.get("market_analysis_required", True)
            confidence_threshold = kwargs.get("confidence_threshold", 60.0)
            mortgage_compliance_check = kwargs.get("mortgage_compliance_check", True)
            
            # Convert dictionary to PropertyDetails dataclass
            property_details = PropertyDetails(**property_details_dict)
            
            # Simulate processing time
            await asyncio.sleep(0.5)
            
            # Perform property valuation
            result = await self._estimate_property_value(
                property_details,
                valuation_approaches,
                purpose,
                appraisal_document_url,
                comparable_sales_radius_miles,
                comparable_sales_timeframe_months,
                minimum_comparable_sales,
                use_external_avm_apis,
                avm_providers,
                market_analysis_required,
                confidence_threshold,
                mortgage_compliance_check
            )
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result,
                execution_time=0.5
            )
            
        except Exception as e:
            self.logger.error(f"Property valuation failed: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=f"Property valuation failed: {str(e)}",
                execution_time=0.0
            )
            
    async def _estimate_property_value(
        self,
        property_details: PropertyDetails,
        valuation_approaches: List[str],
        purpose: str,
        appraisal_document_url: Optional[str],
        comparable_sales_radius_miles: float,
        comparable_sales_timeframe_months: int,
        minimum_comparable_sales: int,
        use_external_avm_apis: bool,
        avm_providers: List[str],
        market_analysis_required: bool,
        confidence_threshold: float,
        mortgage_compliance_check: bool
    ) -> Dict[str, Any]:
        """Perform comprehensive property valuation."""
        
        # Process appraisal document if provided
        appraisal_data = None
        if appraisal_document_url:
            appraisal_data = await self._process_appraisal_document(appraisal_document_url)
            
        # Get comparable sales
        comparable_sales = await self._get_comparable_sales(
            property_details,
            comparable_sales_radius_miles,
            comparable_sales_timeframe_months,
            minimum_comparable_sales
        )
        
        # Perform market analysis
        market_analysis = None
        if market_analysis_required:
            market_analysis = await self._analyze_market_conditions(property_details)
            
        # Execute valuation approaches
        approach_results = {}
        
        if ValuationApproach.SALES_COMPARISON.value in valuation_approaches:
            approach_results["sales_comparison"] = await self._perform_sales_comparison_approach(
                property_details, comparable_sales
            )
            
        if ValuationApproach.COST_APPROACH.value in valuation_approaches:
            approach_results["cost_approach"] = await self._perform_cost_approach(property_details)
            
        if ValuationApproach.INCOME_APPROACH.value in valuation_approaches:
            approach_results["income_approach"] = await self._perform_income_approach(property_details)
            
        # Get external AVM estimates
        avm_results = []
        if use_external_avm_apis:
            avm_results = await self._get_external_avm_estimates(property_details, avm_providers)
            
        # Reconcile approaches
        primary_estimate = self._reconcile_valuation_approaches(approach_results, avm_results)
        
        # Check confidence threshold
        if primary_estimate["confidence_score"] < confidence_threshold:
            primary_estimate["confidence_warning"] = f"Confidence below threshold ({confidence_threshold}%)"
            
        # Analyze risk factors and recommendations
        risk_analysis = self._analyze_risk_factors_and_recommendations(
            property_details, market_analysis, approach_results
        )
        
        # Calculate quality metrics
        valuation_quality = self._calculate_valuation_quality(
            comparable_sales, market_analysis, approach_results
        )
        
        # Mortgage lending analysis
        mortgage_lending_analysis = None
        if mortgage_compliance_check:
            mortgage_lending_analysis = self._perform_mortgage_lending_analysis(
                primary_estimate, risk_analysis, valuation_quality
            )
            
        # Property insights
        property_insights = self._generate_property_insights(
            property_details, market_analysis, primary_estimate
        )
        
        # Calculate AVM consensus if multiple AVM results
        avm_consensus_value = None
        avm_confidence_weighted_average = None
        if len(avm_results) > 1:
            avm_consensus_value = sum(avm["estimated_value"] for avm in avm_results) / len(avm_results)
            total_weight = sum(avm["confidence_score"] for avm in avm_results)
            if total_weight > 0:
                avm_confidence_weighted_average = sum(
                    avm["estimated_value"] * avm["confidence_score"] for avm in avm_results
                ) / total_weight
                
        # Compile final result
        result = {
            "property_address": property_details.address,
            "valuation_date": datetime.now().isoformat(),
            "purpose": purpose,
            "primary_estimate": primary_estimate,
            "approach_results": approach_results,
            "avm_results": avm_results,
            "avm_consensus_value": avm_consensus_value,
            "avm_confidence_weighted_average": avm_confidence_weighted_average,
            "market_analysis": market_analysis.__dict__ if market_analysis else None,
            "valuation_quality": valuation_quality.__dict__,
            "risk_factors": risk_analysis["risk_factors"],
            "valuation_limitations": risk_analysis["limitations"],
            "recommendations": risk_analysis["recommendations"],
            "mortgage_lending_analysis": mortgage_lending_analysis,
            "property_insights": property_insights.__dict__,
            "data_sources_used": self._get_data_sources_used(valuation_approaches, use_external_avm_apis),
            "analysis_notes": [
                f"Valuation completed using {len(valuation_approaches)} approach(es)",
                f"Analysis based on {len(comparable_sales)} comparable sales",
                f"Overall confidence: {primary_estimate['confidence_score']:.1f}%"
            ],
            "expires_date": (datetime.now() + timedelta(days=120)).isoformat(),  # 120 days
            "valuation_summary": {
                "estimated_value": primary_estimate["estimated_value"],
                "confidence_score": primary_estimate["confidence_score"],
                "value_range": primary_estimate["value_range"],
                "primary_approach": primary_estimate["primary_approach"],
                "market_position": property_insights.market_position,
                "key_findings": self._get_key_findings(primary_estimate, market_analysis, property_insights)
            }
        }
        
        return result
        
    async def _process_appraisal_document(self, document_url: str) -> Dict[str, Any]:
        """Process Form 1004 appraisal document (mock implementation)."""
        # TODO: Integrate with Azure Document Intelligence
        return {
            "appraised_value": 450000,
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "property_details": {
                "living_area_sqft": 2200,
                "year_built": 2010,
                "bedrooms": 4,
                "bathrooms": 2.5,
                "property_condition": "good"
            },
            "comparable_sales": [
                {
                    "address": "123 Comparable St",
                    "sale_price": 440000,
                    "sale_date": "2024-12-15",
                    "adjustments": -10000
                }
            ],
            "appraiser_notes": "Property in good condition, market is stable"
        }
        
    async def _get_comparable_sales(
        self,
        property_details: PropertyDetails,
        radius_miles: float,
        timeframe_months: int,
        minimum_sales: int
    ) -> List[ComparableSale]:
        """Get comparable sales data (mock implementation)."""
        
        # Generate mock comparable sales
        base_price = 200 * property_details.living_area_sqft  # Base price per sqft
        
        comparables = []
        for i in range(max(minimum_sales, 4)):
            # Vary the properties slightly
            size_variance = 1.0 + (i - 2) * 0.1  # ±20% size variance
            price_variance = 1.0 + (i - 2) * 0.05  # ±10% price variance
            
            comp_sqft = int(property_details.living_area_sqft * size_variance)
            comp_price = base_price * price_variance * comp_sqft
            
            # Calculate adjustments
            adjustments = AdjustmentFactors(
                time_adjustment=i * 500,  # Time adjustment
                size_adjustment=(comp_sqft - property_details.living_area_sqft) * -50,  # Size adjustment
                condition_adjustment=0,  # Assume similar condition
                location_adjustment=i * 1000,  # Location variance
                feature_adjustments=i * -2000,  # Feature differences
            )
            adjustments.total_adjustment = (
                adjustments.time_adjustment + adjustments.size_adjustment +
                adjustments.condition_adjustment + adjustments.location_adjustment +
                adjustments.feature_adjustments
            )
            
            comparable = ComparableSale(
                address=f"{100 + i * 10} Comparable St",
                distance_miles=0.2 + i * 0.2,
                sale_date=(datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m-%d"),
                sale_price=comp_price,
                living_area_sqft=comp_sqft,
                price_per_sqft=comp_price / comp_sqft,
                bedrooms=property_details.bedrooms + (i % 2 - 1),
                bathrooms=property_details.bathrooms + (i % 3 - 1) * 0.5,
                year_built=property_details.year_built + (i % 5 - 2) * 2,
                property_condition=PropertyCondition.GOOD.value,
                days_on_market=20 + i * 5,
                adjustment_factors=adjustments,
                adjusted_price=comp_price + adjustments.total_adjustment,
                weight_factor=max(0.5, 1.0 - i * 0.1)  # Decreasing weight with distance/time
            )
            
            comparables.append(comparable)
            
        return comparables
        
    async def _analyze_market_conditions(self, property_details: PropertyDetails) -> MarketAnalysis:
        """Analyze market conditions (mock implementation)."""
        return MarketAnalysis(
            market_conditions=MarketCondition.BALANCED_MARKET.value,
            median_home_value=425000.0,
            median_price_per_sqft=195.0,
            year_over_year_appreciation=3.2,
            months_of_inventory=4.5,
            average_days_on_market=28,
            price_trend_6_months=PriceTrend.INCREASING.value,
            price_trend_12_months=PriceTrend.INCREASING.value,
            seasonal_adjustment_factor=1.02,
            neighborhood_desirability_score=7.5,
            school_district_rating=8.0,
            walkability_score=65,
            crime_index=25
        )
        
    async def _perform_sales_comparison_approach(
        self, property_details: PropertyDetails, comparables: List[ComparableSale]
    ) -> Dict[str, Any]:
        """Perform sales comparison approach valuation."""
        
        if not comparables:
            raise ValueError("No comparable sales available for sales comparison approach")
            
        # Calculate weighted average of adjusted comparable prices
        weighted_sum = sum(comp.adjusted_price * comp.weight_factor for comp in comparables)
        total_weight = sum(comp.weight_factor for comp in comparables)
        
        estimated_value = round(weighted_sum / total_weight)
        average_price_per_sqft = round(estimated_value / property_details.living_area_sqft)
        
        # Calculate confidence based on comparables quality
        confidence = min(95, 60 + len(comparables) * 10 + 
                        len([c for c in comparables if c.weight_factor > 0.8]) * 5)
        
        return {
            "estimated_value": estimated_value,
            "confidence_score": confidence,
            "comparable_sales": [
                {
                    "address": comp.address,
                    "distance_miles": comp.distance_miles,
                    "sale_date": comp.sale_date,
                    "sale_price": comp.sale_price,
                    "adjusted_price": comp.adjusted_price,
                    "weight_factor": comp.weight_factor,
                    "adjustment_factors": comp.adjustment_factors.__dict__ if comp.adjustment_factors else {}
                }
                for comp in comparables
            ],
            "average_price_per_sqft": average_price_per_sqft,
            "adjustment_summary": f"Analysis based on {len(comparables)} comparable sales with weighted adjustments"
        }
        
    async def _perform_cost_approach(self, property_details: PropertyDetails) -> Dict[str, Any]:
        """Perform cost approach valuation."""
        
        # Simplified cost approach calculation
        land_value_per_sqft = 50.0  # Mock land value
        lot_size = property_details.lot_size_sqft or 8000
        land_value = lot_size * land_value_per_sqft
        
        construction_cost_per_sqft = 150.0  # Mock construction cost
        replacement_cost_new = property_details.living_area_sqft * construction_cost_per_sqft
        
        # Calculate depreciation
        property_age = datetime.now().year - property_details.year_built
        economic_life = 50  # years
        depreciation_rate = min(property_age / economic_life, 0.8)
        depreciation_amount = replacement_cost_new * depreciation_rate
        
        estimated_value = round(land_value + replacement_cost_new - depreciation_amount)
        
        return {
            "estimated_value": estimated_value,
            "land_value": land_value,
            "replacement_cost_new": replacement_cost_new,
            "depreciation_amount": depreciation_amount,
            "confidence_score": 70.0  # Cost approach typically has moderate confidence
        }
        
    async def _perform_income_approach(self, property_details: PropertyDetails) -> Dict[str, Any]:
        """Perform income approach valuation (for investment properties)."""
        
        # Mock rental analysis
        monthly_rent_per_sqft = 1.5  # Mock rental rate
        monthly_rental_estimate = round(property_details.living_area_sqft * monthly_rent_per_sqft)
        annual_rental_income = monthly_rental_estimate * 12
        
        # Apply capitalization rate
        cap_rate = 0.06  # 6% cap rate
        estimated_value = round(annual_rental_income / cap_rate)
        
        return {
            "estimated_value": estimated_value,
            "monthly_rental_estimate": monthly_rental_estimate,
            "annual_rental_income": annual_rental_income,
            "capitalization_rate": cap_rate,
            "confidence_score": 65.0  # Income approach confidence varies by market data
        }
        
    async def _get_external_avm_estimates(
        self, property_details: PropertyDetails, providers: List[str]
    ) -> List[Dict[str, Any]]:
        """Get external AVM estimates (mock implementation)."""
        
        avm_results = []
        base_value = 200 * property_details.living_area_sqft
        
        if "zillow" in providers:
            avm_results.append({
                "avm_provider": "Zillow Zestimate",
                "estimated_value": round(base_value * 1.02),
                "confidence_score": 82.0,
                "value_range": {
                    "low_estimate": round(base_value * 0.95),
                    "high_estimate": round(base_value * 1.08)
                },
                "forecast_change_12_months": 2.5,
                "data_quality_score": 85.0,
                "comparable_sales_count": 12,
                "last_updated": datetime.now().isoformat()
            })
            
        if "attom" in providers:
            avm_results.append({
                "avm_provider": "ATTOM Data",
                "estimated_value": round(base_value * 0.98),
                "confidence_score": 78.0,
                "value_range": {
                    "low_estimate": round(base_value * 0.92),
                    "high_estimate": round(base_value * 1.05)
                },
                "forecast_change_12_months": 1.8,
                "data_quality_score": 82.0,
                "comparable_sales_count": 8,
                "last_updated": datetime.now().isoformat()
            })
            
        if "corelogic" in providers:
            avm_results.append({
                "avm_provider": "CoreLogic",
                "estimated_value": round(base_value * 1.01),
                "confidence_score": 85.0,
                "value_range": {
                    "low_estimate": round(base_value * 0.96),
                    "high_estimate": round(base_value * 1.06)
                },
                "data_quality_score": 88.0,
                "comparable_sales_count": 15,
                "last_updated": datetime.now().isoformat()
            })
            
        return avm_results
        
    def _reconcile_valuation_approaches(
        self, approach_results: Dict[str, Any], avm_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reconcile multiple valuation approaches."""
        
        estimates = []
        
        # Add approach results
        for approach, result in approach_results.items():
            estimates.append({
                "value": result["estimated_value"],
                "confidence": result["confidence_score"],
                "approach": approach
            })
            
        # Add AVM results
        for avm in avm_results:
            estimates.append({
                "value": avm["estimated_value"],
                "confidence": avm["confidence_score"],
                "approach": f"avm_{avm['avm_provider'].lower().replace(' ', '_')}"
            })
            
        if not estimates:
            raise ValueError("No valuation estimates available for reconciliation")
            
        # Weight estimates by confidence
        weighted_sum = sum(est["value"] * (est["confidence"] / 100) for est in estimates)
        total_weight = sum(est["confidence"] / 100 for est in estimates)
        
        reconciled_value = round(weighted_sum / total_weight)
        overall_confidence = round(sum(est["confidence"] for est in estimates) / len(estimates), 1)
        
        # Find primary approach (highest confidence)
        primary_approach = max(estimates, key=lambda x: x["confidence"])["approach"]
        
        # Calculate value range (±10% based on confidence)
        range_factor = (100 - overall_confidence) / 1000 + 0.05  # 5-15% range
        low_estimate = round(reconciled_value * (1 - range_factor))
        high_estimate = round(reconciled_value * (1 + range_factor))
        
        return {
            "estimated_value": reconciled_value,
            "confidence_score": overall_confidence,
            "value_range": {
                "low_estimate": low_estimate,
                "high_estimate": high_estimate
            },
            "primary_approach": primary_approach,
            "reconciliation_method": "confidence_weighted_average"
        }
        
    def _analyze_risk_factors_and_recommendations(
        self,
        property_details: PropertyDetails,
        market_analysis: Optional[MarketAnalysis],
        approach_results: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Analyze risk factors and generate recommendations."""
        
        risk_factors = []
        recommendations = []
        limitations = []
        
        # Analyze property age
        property_age = datetime.now().year - property_details.year_built
        if property_age > 30:
            risk_factors.append("Property age over 30 years may require additional maintenance considerations")
            
        # Market conditions
        if market_analysis:
            if market_analysis.months_of_inventory > 6:
                risk_factors.append("High inventory levels indicate potential for price pressure")
                
            if market_analysis.average_days_on_market > 60:
                risk_factors.append("Extended marketing times in current market conditions")
                
        # Property condition
        if property_details.property_condition in [PropertyCondition.FAIR.value, PropertyCondition.POOR.value]:
            risk_factors.append("Property condition may impact marketability and value")
            recommendations.append("Consider property inspection and repair cost estimates")
            
        # General recommendations
        recommendations.extend([
            "Verify all property details through on-site inspection",
            "Consider additional market research for unique property features",
            "Review recent comparable sales for accuracy"
        ])
        
        # Limitations
        limitations.extend([
            "Valuation based on available market data as of analysis date",
            "External factors such as interest rates and economic conditions may impact actual market value",
            "Property condition assessment based on available information only"
        ])
        
        return {
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "limitations": limitations
        }
        
    def _calculate_valuation_quality(
        self,
        comparable_sales: List[ComparableSale],
        market_analysis: Optional[MarketAnalysis],
        approach_results: Dict[str, Any]
    ) -> ValuationQuality:
        """Calculate valuation quality metrics."""
        
        # Data quality score based on available data
        data_quality_score = 80.0
        if market_analysis:
            data_quality_score += 10.0
        if len(approach_results) > 1:
            data_quality_score += 5.0
            
        # Comparable quality score
        comparable_quality_score = min(90.0, 60.0 + len(comparable_sales) * 10.0)
        
        # Market data recency score
        market_data_recency_score = 85.0  # Mock score
        
        # Methodology reliability score
        methodology_reliability_score = 80.0
        if "sales_comparison" in approach_results:
            methodology_reliability_score += 5.0
        if len(approach_results) > 2:
            methodology_reliability_score += 5.0
            
        # Overall confidence
        overall_confidence = (
            data_quality_score * 0.3 +
            comparable_quality_score * 0.3 +
            market_data_recency_score * 0.2 +
            methodology_reliability_score * 0.2
        )
        
        return ValuationQuality(
            data_quality_score=data_quality_score,
            comparable_quality_score=comparable_quality_score,
            market_data_recency_score=market_data_recency_score,
            methodology_reliability_score=methodology_reliability_score,
            overall_confidence=overall_confidence
        )
        
    def _perform_mortgage_lending_analysis(
        self,
        primary_estimate: Dict[str, Any],
        risk_analysis: Dict[str, List[str]],
        valuation_quality: ValuationQuality
    ) -> Dict[str, Any]:
        """Perform mortgage lending compliance analysis."""
        
        confidence = primary_estimate["confidence_score"]
        
        return {
            "fnma_compliance": confidence >= 70,
            "fhlmc_compliance": confidence >= 70,
            "recommended_ltv_limit": 95 if confidence >= 80 else 90,
            "valuation_concerns": risk_analysis["risk_factors"],
            "additional_review_required": confidence < 70 or len(risk_analysis["risk_factors"]) > 3,
            "appraisal_recommended": confidence < 75,
            "desktop_review_acceptable": confidence >= 85
        }
        
    def _generate_property_insights(
        self,
        property_details: PropertyDetails,
        market_analysis: Optional[MarketAnalysis],
        primary_estimate: Dict[str, Any]
    ) -> PropertyInsights:
        """Generate property insights and recommendations."""
        
        value_drivers = ["Location", "Property size", "Market conditions"]
        value_detractors = []
        improvement_recommendations = ["Regular maintenance", "Energy efficiency upgrades"]
        
        # Property age considerations
        property_age = datetime.now().year - property_details.year_built
        if property_age < 10:
            value_drivers.append("Newer construction")
        elif property_age > 30:
            value_detractors.append("Property age")
            improvement_recommendations.append("Consider major system updates")
            
        # Property features
        if property_details.garage_spaces and property_details.garage_spaces > 0:
            value_drivers.append("Garage parking")
        if property_details.pool:
            value_drivers.append("Swimming pool")
        if property_details.fireplace_count and property_details.fireplace_count > 0:
            value_drivers.append("Fireplace(s)")
            
        # Market position
        market_position = MarketPosition.AT_MARKET.value
        if market_analysis:
            estimated_price_per_sqft = primary_estimate["estimated_value"] / property_details.living_area_sqft
            if estimated_price_per_sqft > market_analysis.median_price_per_sqft * 1.1:
                market_position = MarketPosition.ABOVE_MARKET.value
            elif estimated_price_per_sqft < market_analysis.median_price_per_sqft * 0.9:
                market_position = MarketPosition.BELOW_MARKET.value
                
        return PropertyInsights(
            value_drivers=value_drivers,
            value_detractors=value_detractors,
            improvement_recommendations=improvement_recommendations,
            market_position=market_position
        )
        
    def _get_data_sources_used(self, valuation_approaches: List[str], use_external_avm_apis: bool) -> List[str]:
        """Get list of data sources used."""
        sources = ["property_records", "market_data"]
        
        if ValuationApproach.SALES_COMPARISON.value in valuation_approaches:
            sources.extend(["mls_data", "comparable_sales"])
        if use_external_avm_apis:
            sources.append("external_avm_apis")
            
        return sources
        
    def _get_key_findings(
        self,
        primary_estimate: Dict[str, Any],
        market_analysis: Optional[MarketAnalysis],
        property_insights: PropertyInsights
    ) -> List[str]:
        """Get key findings from valuation."""
        
        findings = [
            f"Estimated value: ${primary_estimate['estimated_value']:,}",
            f"Confidence level: {primary_estimate['confidence_score']:.1f}%",
            f"Primary approach: {primary_estimate['primary_approach'].replace('_', ' ').title()}"
        ]
        
        if market_analysis:
            findings.append(f"Market conditions: {market_analysis.market_conditions.replace('_', ' ').title()}")
            
        findings.append(f"Market position: {property_insights.market_position.replace('_', ' ').title()}")
        
        if property_insights.value_drivers:
            findings.append(f"Key value drivers: {', '.join(property_insights.value_drivers[:3])}")
            
        return findings
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Get comprehensive tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.metadata.version,
            "property_types": [pt.value for pt in PropertyType],
            "valuation_approaches": [va.value for va in ValuationApproach],
            "property_conditions": [pc.value for pc in PropertyCondition],
            "features": {
                "sales_comparison_approach": True,
                "cost_approach": True,
                "income_approach": True,
                "automated_valuation_model": True,
                "market_analysis": True,
                "comparable_sales_analysis": True,
                "risk_assessment": True,
                "mortgage_compliance_check": True,
                "property_insights": True,
                "confidence_scoring": True,
                "value_range_estimation": True
            },
            "supported_purposes": [
                "purchase", "refinance", "home_equity", "insurance", "tax_assessment", "investment"
            ],
            "avm_providers": ["zillow", "attom", "corelogic", "realtytrac"],
            "parameters_schema": self.get_parameters_schema()
        }