# GEORGENSEN COURIER - DETAILED FINANCIAL MODEL & ANALYSIS

**February 10, 2026 | Comprehensive 36-Month Projection**

---

## EXECUTIVE FINANCIAL SUMMARY

### Investment Required: $1.5M
```
Product Development:    $400K (platform, mobile, integrations)
Operations Setup:       $300K (team hiring, infrastructure)
Customer Acquisition:   $500K (marketing, partnerships)
Working Capital:        $300K (payment processing, reserves)
```

### Projected Returns
```
Year 1: -$1.1M (investment phase, 50K orders)
Year 2: +$1.2M (growth phase, 500K orders)
Year 3: +$8.4M (scale phase, 2M orders)
Year 5: $45M+ revenue (potential market leader)
```

### Key Assumptions
- Pricing: $16.50 average order value (AOV)
- Margins: 30% platform take after partner payout
- Growth: 15% MoM Year 1, 8% MoM Year 2, 5% MoM Year 3
- Churn: 40% annual (high in Year 1, improving to 20% by Year 3)
- CAC: $75 in Year 1, declining to $25 by Year 3

---

## DETAILED FINANCIAL MODEL (36 MONTHS)

### REVENUE PROJECTIONS

#### Monthly Order Forecast

```
                    Year 1              Year 2              Year 3
├─ Q1 (Jan-Mar)
│  ├─ Jan: 1,000    ├─ Jan: 30,000      ├─ Jan: 120,000
│  ├─ Feb: 2,000    ├─ Feb: 35,000      ├─ Feb: 125,000
│  └─ Mar: 3,500    └─ Mar: 40,000      └─ Mar: 130,000
│  Q1 Total: 6,500   Q1 Total: 105,000  Q1 Total: 375,000

├─ Q2 (Apr-Jun)
│  ├─ Apr: 5,000    ├─ Apr: 50,000      ├─ Apr: 135,000
│  ├─ May: 8,000    ├─ May: 65,000      ├─ May: 140,000
│  └─ Jun: 12,000   └─ Jun: 80,000      └─ Jun: 145,000
│  Q2 Total: 25,000  Q2 Total: 195,000  Q2 Total: 420,000

├─ Q3 (Jul-Sep)
│  ├─ Jul: 18,000   ├─ Jul: 100,000     ├─ Jul: 150,000
│  ├─ Aug: 22,000   ├─ Aug: 120,000     ├─ Aug: 160,000
│  └─ Sep: 26,000   └─ Sep: 140,000     └─ Sep: 165,000
│  Q3 Total: 66,000  Q3 Total: 360,000  Q3 Total: 475,000

└─ Q4 (Oct-Dec)
   ├─ Oct: 30,000   ├─ Oct: 160,000     ├─ Oct: 170,000
   ├─ Nov: 35,000   ├─ Nov: 180,000     ├─ Nov: 175,000
   └─ Dec: 40,000   └─ Dec: 200,000     └─ Dec: 185,000
   Q4 Total: 105,000 Q4 Total: 540,000  Q4 Total: 530,000

Year Total: 202,500 Year Total: 1,200,000 Year Total: 1,800,000
Monthly Avg: 16,875  Monthly Avg: 100,000   Monthly Avg: 150,000
Daily Avg:   556     Daily Avg:   3,333     Daily Avg:   5,000
```

#### Revenue Recognition

```
Monthly Revenue Calculation:
├─ Orders processed: 16,875 (Year 1 average)
├─ Average order value: $16.50
├─ Gross GMV: $278,438
├─ Platform take (30% after partner payout): $83,531
├─ Less: Stripe processing (3% + $0.30): -$8,353
├─ Net Monthly Revenue: $75,178

Year 1 Quarterly Breakdown:

Q1: 6,500 orders × $16.50 × 27% margin = $28,935 (3-month avg)
Q2: 25,000 orders × $16.50 × 27% margin = $111,375
Q3: 66,000 orders × $16.50 × 27% margin = $294,030
Q4: 105,000 orders × $16.50 × 27% margin = $468,225

Year 1 Total Revenue: $902,565
(actual projection with ramp-up effects)

Year 2 Total Revenue: $2,700,000
(more conservative: 1.2M orders due to slower growth mid-year)

Year 3 Total Revenue: $4,050,000
(1.8M orders, improved margins 30%+)
```

---

## COST STRUCTURE & EXPENSE PROJECTIONS

### FIXED COSTS (Monthly)

#### Infrastructure Costs

```
Year 1 (MVP Phase):
├─ Cloud hosting (AWS/GCP t2.large EC2): $200/month
│  └─ 1 backend instance + 1 DB instance
├─ RDS PostgreSQL (db.t3.micro): $25/month
├─ S3 storage (100GB POD files): $2.30/month
├─ CloudFront CDN (10TB/month): $150/month
├─ DNS (Route53): $1/month
├─ SSL certificate (Let's Encrypt): free
├─ Total Year 1: $378/month → $4,536/year

Year 2 (Growth Phase):
├─ Kubernetes cluster (3 nodes): $1,500/month
├─ RDS PostgreSQL (db.t3.small + read replica): $150/month
├─ S3 storage (500GB): $12/month
├─ CloudFront CDN (50TB/month): $600/month
├─ ElasticsearchCache (Datadog logs): $400/month
├─ Redis (AWS ElastiCache, cache.t3.small): $30/month
├─ Total Year 2: $2,692/month → $32,304/year

Year 3 (Scale Phase):
├─ Kubernetes cluster (20 nodes): $8,000/month
├─ RDS PostgreSQL (db.r5.large HA): $800/month
├─ S3 storage (2TB): $48/month
├─ CloudFront CDN (200TB/month): $2,500/month
├─ Monitoring (Datadog enterprise): $2,000/month
├─ Redis cluster (cache.r6g.large): $500/month
├─ Total Year 3: $13,848/month → $166,176/year
```

#### Team Payroll

```
Year 1 (Lean Team):
├─ CTO (0.5 FTE salary): $4,000/month → $48K/year
├─ 1 Backend engineer: $3,500/month → $42K/year
├─ 1 Frontend engineer: $3,000/month → $36K/year
├─ 1 DevOps/Operations: $3,500/month → $42K/year
├─ 2 Support agents (Part-time): $2,000/month → $24K/year
├─ Taxes & benefits (30%): $4,470/month
├─ Total: $20,970/month → $251,640/year

Year 2 (Scaling Team):
├─ CTO (1.0 FTE): $8,000/month
├─ 2 Backend engineers: $7,000/month
├─ 2 Frontend engineers: $6,000/month
├─ 1 DevOps engineer: $3,500/month
├─ 1 Product manager: $4,000/month
├─ 3 Support agents (Full-time): $6,000/month
├─ 1 Finance/Operations: $3,000/month
├─ Taxes & benefits (30%): $11,550/month
├─ Total: $49,050/month → $588,600/year

Year 3 (Professional Team):
├─ VP Engineering: $10,000/month
├─ 4 Backend engineers: $14,000/month
├─ 3 Frontend engineers: $9,000/month
├─ 2 DevOps engineers: $7,000/month
├─ 1 Product manager: $4,000/month
├─ 1 Data engineer: $4,000/month
├─ 5 Support agents + 1 manager: $15,000/month
├─ 1 Operations manager: $4,000/month
├─ Taxes & benefits (35%): $20,300/month
├─ Total: $88,300/month → $1,059,600/year
```

#### Professional Services & Licenses

```
Year 1:
├─ Legal (contract review): $2,000
├─ Accounting: $1,500/month → $18,000/year
├─ Insurance (liability + cyber): $500/month → $6,000/year
├─ Email service (SendGrid): $500/month → $6,000/year
├─ Monitoring tools (New Relic): $300/month → $3,600/year
├─ Error tracking (Sentry): $300/month → $3,600/year
└─ Total: $37,200/year

Year 2:
├─ Legal (IP + compliance): $5,000/year
├─ Accounting: $2,000/month → $24,000/year
├─ Insurance: $1,500/month → $18,000/year
├─ Email service: $2,000/month → $24,000/year
├─ Monitoring (Datadog): $2,000/month → $24,000/year
├─ Security audit (annual): $10,000/year
└─ Total: $105,000/year

Year 3:
├─ Legal: $15,000/year
├─ Accounting: $3,000/month → $36,000/year
├─ Insurance: $3,000/month → $36,000/year
├─ Email service: $5,000/month → $60,000/year
├─ Monitoring: $5,000/month → $60,000/year
├─ Security audit + penetration testing: $25,000/year
├─ Compliance (SOC 2, ISO 27001): $20,000/year
└─ Total: $252,000/year
```

#### Total Monthly Fixed Costs

```
Year 1: $378 + $20,970 + $3,100 = $24,448/month = $293,376/year
Year 2: $2,692 + $49,050 + $8,750 = $60,492/month = $725,904/year
Year 3: $13,848 + $88,300 + $21,000 = $123,148/month = $1,477,776/year
```

### VARIABLE COSTS (Per Order)

#### Payment Processing

```
Stripe Processing:
├─ Card fee: 2.9% per transaction
├─ Fixed fee: $0.30 per transaction
├─ For $16.50 order: $0.478 + $0.30 = $0.778 (4.7%)
├─ Alternative (ACH): 1% + $0.25 (lower for B2B)
├─ Refund cost: Same as original transaction fee
└─ Chargeback fee: $15 per disputed transaction (assume 0.1%)

Per-order impact:
├─ Successful payment: $0.778
├─ Failed payment retry: +$0.30 (assume 2% failure rate)
├─ Chargeback reserve (0.1% × $0.778 + $15): +$0.02
└─ Total payment cost: $0.81 per order
```

#### Partner Payout & Logistics

```
Partner Commission:
├─ Local delivery: 70% of order value
├─ Intercity delivery: 60% of order value (platform handles more)
├─ International: 50% (platform arranges logistics)

For $16.50 average order:
├─ Partner payout (70%): $11.55
├─ Customer acquisition cost amortization: $0.21
│  (assumes $75 CAC, LTV of 10 orders)
├─ Insurance reserve (0.5%): $0.08
├─ Fraud losses (0.5%): $0.08
└─ Total variable cost: $11.92

Platform proceeds: $16.50 - $11.92 = $4.58 (27.8% margin)
```

#### Customer Support

```
Support Cost Per Order:
├─ Tier 1 (Automated FAQ): 0% orders = $0 (chatbot)
├─ Tier 2 (Email support): 2% orders = $0.15
│  (5 min @ $30/hour = $2.50 agent cost)
├─ Tier 3 (Phone/escalation): 0.5% orders = $0.20
├─ Dispute handling: 2% orders = $0.50
│  (requires investigation, potential refund)
└─ Total support cost: $0.85 per order

Support cost percentage: 5.2% of order value
```

#### Total Variable Cost Per Order

```
Payment processing:     $0.81
Partner payout:        $11.55
Customer acquisition:   $0.21
Fraud/Insurance:        $0.16
Support:               $0.85
────────────────────────────
Total:                $13.58 (82.3% of order value)

Platform revenue:       $4.92 (29.8% - close to 30% target)
```

### YEAR-BY-YEAR P&L PROJECTION

#### Year 1 Summary

```
                           Q1         Q2         Q3         Q4       TOTAL
───────────────────────────────────────────────────────────────────────────
Orders Processed:         6,500     25,000     66,000    105,000   202,500
Average Order Value:     $16.50    $16.50     $16.50     $16.50    $16.50
───────────────────────────────────────────────────────────────────────────
Gross Revenue:          $107,250  $412,500  $1,089,000  $1,732,500  $3,341,250
Platform Revenue (28.1%): $30,140  $115,913  $306,049   $487,214   $939,316
───────────────────────────────────────────────────────────────────────────

OPERATING EXPENSES
Fixed Costs:             $73,344  $73,344    $73,344    $73,344   $293,376
  ├─ Infrastructure     $1,134   $1,134     $1,134     $1,134    $4,536
  ├─ Payroll           $62,910  $62,910    $62,910    $62,910   $251,640
  └─ Services/Tools    $9,300   $9,300     $9,300     $9,300    $37,200

Variable Costs:
  ├─ Payment processing  $5,188  $19,200    $50,688    $80,640   $155,716
  ├─ Fraud/Disputes      $1,040   $4,000    $10,560    $16,800   $32,400
  ├─ Customer Support    $5,525  $21,250    $56,100    $89,250   $172,125
  └─ Subtotal:         $11,753  $44,450   $117,348   $186,690   $360,241

───────────────────────────────────────────────────────────────────────────
EBITDA:                -$55,957  -$2,481   $115,357   $227,180  $284,099
EBITDA Margin:           -185%     -2%       38%        47%        30%
───────────────────────────────────────────────────────────────────────────

Marketing & CAC:          $37,500 $37,500   $37,500   $37,500   $150,000
  └─ At $75 CAC, ~500 new customers/quarter

EBITDA after Marketing: -$93,457 -$40,981  $77,857   $189,680  $134,099
───────────────────────────────────────────────────────────────────────────

Cumulative EBITDA deficit at end of Year 1: -$750,000 (with ramp)
```

#### Year 2 Summary

```
                         Jan-Mar   Apr-Jun   Jul-Sep   Oct-Dec   TOTAL
───────────────────────────────────────────────────────────────────────────
Orders Processed:        105,000   195,000   360,000   540,000   1,200,000
Average Order Value:      $16.50   $16.50    $16.50    $16.50    $16.50
───────────────────────────────────────────────────────────────────────────
Gross Revenue:         $1,732,500 $3,217,500 $5,940,000 $8,910,000 $19,800,000
Platform Revenue (28.1%): $486,923 $904,123  $1,670,040 $2,503,530 $5,564,616
───────────────────────────────────────────────────────────────────────────

OPERATING EXPENSES
Fixed Costs:             $181,476 $181,476  $181,476  $181,476  $725,904
  ├─ Infrastructure       $8,076   $8,076    $8,076    $8,076   $32,304
  ├─ Payroll            $147,150 $147,150  $147,150  $147,150  $588,600
  └─ Services/Tools      $26,250  $26,250   $26,250   $26,250  $105,000

Variable Costs:
  ├─ Payment processing   $83,640 $155,160  $286,560  $429,840 $955,200
  ├─ Fraud/Disputes       $8,400  $15,600   $28,800   $43,200  $96,000
  ├─ Customer Support    $89,250 $165,750  $306,000  $459,000 $1,020,000
  └─ Subtotal:          $181,290 $336,510  $621,360  $932,040 $2,071,200

───────────────────────────────────────────────────────────────────────────
EBITDA:                 $124,157 $386,137  $867,204 $1,390,014 $2,767,512
EBITDA Margin:              25%      43%       52%       55%        50%
───────────────────────────────────────────────────────────────────────────

Marketing & CAC:          $30,000  $60,000  $90,000  $120,000  $300,000
  └─ Declining CAC to $40-50, more selective

EBITDA after Marketing:   $94,157 $326,137  $777,204 $1,270,014 $2,467,512
───────────────────────────────────────────────────────────────────────────

BREAK-EVEN ACHIEVED: Q2 Year 2
Cumulative EBITDA: Return to positive territory
```

#### Year 3 Summary

```
                         Jan-Mar   Apr-Jun   Jul-Sep   Oct-Dec   TOTAL
───────────────────────────────────────────────────────────────────────────
Orders Processed:        375,000   420,000   475,000   530,000   1,800,000
Average Order Value:      $16.50   $16.50    $16.50    $16.50    $16.50
───────────────────────────────────────────────────────────────────────────
Gross Revenue:         $6,187,500 $6,930,000 $7,837,500 $8,745,000 $29,700,000
Platform Revenue (30%):  $1,856,250 $2,079,000 $2,351,250 $2,623,500 $8,910,000
───────────────────────────────────────────────────────────────────────────

OPERATING EXPENSES
Fixed Costs:             $369,444 $369,444  $369,444  $369,444 $1,477,776
  ├─ Infrastructure      $41,544  $41,544   $41,544   $41,544  $166,176
  ├─ Payroll            $264,900 $264,900  $264,900  $264,900 $1,059,600
  └─ Services/Tools      $63,000  $63,000   $63,000   $63,000  $252,000

Variable Costs:
  ├─ Payment processing  $300,000 $337,500  $382,500  $427,500 $1,447,500
  ├─ Fraud/Disputes      $18,000  $20,160   $22,800   $25,440  $86,400
  ├─ Customer Support   $318,750 $357,000  $404,250  $450,550 $1,530,550
  └─ Subtotal:          $636,750 $714,660  $809,550  $903,490 $3,064,450

───────────────────────────────────────────────────────────────────────────
EBITDA:                 $849,056 $994,896 $1,172,256 $1,348,566 $4,364,774
EBITDA Margin:              46%      48%       50%       51%        49%
───────────────────────────────────────────────────────────────────────────

Marketing & CAC:          $50,000  $50,000  $50,000   $50,000  $200,000
  └─ Brand established, less paid acquisition needed

EBITDA after Marketing:   $799,056 $944,896 $1,122,256 $1,298,566 $4,164,774
EBITDA Margin after Marketing: 43%  45%     47%       49%       47%
───────────────────────────────────────────────────────────────────────────
```

---

## CASH FLOW ANALYSIS

### 36-Month Cumulative Cash Position

```
Start:                               $1,500,000 (funding)
├─ Year 1 EBITDA:                     -$750,000
│  CASH at end of Y1:                 $750,000
├─ Year 2 EBITDA:                   +$2,467,512
│  CASH at end of Y2:               $3,217,512
└─ Year 3 EBITDA (9 months):        +$3,123,581 (through Sept)
   CASH at end of month 30:         $6,341,093

Runway Analysis:
├─ Monthly burn (Year 1 avg):        -$62,500
├─ Months of runway from initial funding: 24 months
├─ Break-even achieved: Month 15 (Q2 Year 2)
└─ Positive cash generation: Ongoing after break-even
```

### Payment Terms & Working Capital

```
Receivables (Customer to Platform):
├─ Payment method: Credit card (Stripe) - immediate settlement
├─ Days Sales Outstanding (DSO): 0 days (collected upfront)
├─ Exception: B2B invoicing (5-10 customers) - 30 days
├─ Estimated working capital need: Minimal (<$10K)

Payables (Platform to Partners):
├─ Payment frequency: Weekly or monthly
├─ Days Payable Outstanding (DPO): 7 days
├─ Payout: 70% of order value (after fees)
├─ Impact: Partner payouts must be funded during growth

Cash Conversion Cycle: -7 days (favorable)
├─ Customers pay immediately, partners paid weekly
├─ Platform holds 7-day float for reinvestment
└─ As volume grows: 70% × $1.2M/month = $840K float available
```

---

## SENSITIVITY ANALYSIS

### Key Assumptions Impact on Profitability

#### Scenario 1: Conservative Case (-30% orders)

```
Year 2 adjusted orders: 840,000 (vs. 1.2M base)
Platform revenue: $3,894,931 (vs. $5.6M)
EBITDA: $1,289,458 (vs. $2.47M)
EBITDA margin: 33% (vs. 44%)
Result: Break-even delayed to Q3 Year 2 (vs. Q2)
Runway impact: Still achieves profitability by Year 2
```

#### Scenario 2: Optimistic Case (+50% orders)

```
Year 2 adjusted orders: 1.8M (vs. 1.2M base)
Platform revenue: $8,346,924 (vs. $5.6M)
EBITDA: $4,206,456 (vs. $2.47M)
EBITDA margin: 50% (vs. 44%)
Result: Break-even accelerated to Q1 Year 2 (vs. Q2)
Runway impact: Significantly improves profitability outlook
```

#### Scenario 3: Price Sensitivity (-10% AOV)

```
Average order value: $14.85 (vs. $16.50)
Year 2 revenue impact: -$593,000
EBITDA impact: -$296,500 (half of revenue change due to fixed costs)
Result: Break-even delayed ~1 month
Mitigation: Volume growth can offset price declines
```

#### Scenario 4: Partner Payout Pressure (-5%)

```
If partners demand 75% payout (vs. 70%):
Platform margin: 24% (vs. 30%)
Year 2 EBITDA: $1,870,000 (vs. $2.47M) = -24% impact
Result: Still profitable but materially affected
Required mitigation: Increase volume or reduce operating costs
```

#### Scenario 5: Customer Acquisition Cost Increase (+50%)

```
CAC Year 1: $112.50 (vs. $75)
CAC Year 2: $75 (vs. $50)
Additional annual marketing spend: $150,000
Year 2 EBITDA: $2,317,512 (vs. $2.47M) = -6% impact
Result: Modest impact due to improving LTV/CAC ratio
```

---

## FUNDING & USE OF PROCEEDS

### $1.5M Seed Funding Allocation

```
Product Development: $400K (27%)
├─ Backend infrastructure setup: $100K
│  └─ AWS/GCP/Azure initial setup, VPC security, RDS
├─ Frontend application + mobile MVP: $150K
│  └─ iOS/Android native development or React Native
├─ Third-party integrations: $100K
│  └─ Stripe, email providers, SMS, logistics APIs
└─ QA & DevOps: $50K
   └─ Testing infrastructure, monitoring tools

Operations & People: $500K (33%)
├─ Initial team hiring (12 months): $300K
│  └─ CTO, engineers, support staff (salaries + benefits)
├─ Office & tools: $50K
│  └─ Office space, equipment, software licenses
├─ Legal & Compliance: $100K
│  └─ Incorporation, contracts, insurance, banking setup
└─ Training & onboarding: $50K
   └─ Staff training, partner onboarding procedures

Customer Acquisition: $500K (33%)
├─ Digital marketing: $250K
│  └─ Google Ads, social media, content marketing
├─ Partnership & BD: $150K
│  └─ Conferences, events, B2B sales
└─ Initial promotions: $100K
   └─ First-customer discounts, referral programs

Working Capital & Reserves: $100K (7%)
├─ Payment processing float: $50K
├─ Contingency reserves: $30K
└─ Legal/regulatory reserves: $20K

TOTAL: $1,500,000
```

---

## VALUATION & EXIT SCENARIOS

### Business Valuation (Post-Funding)

```
Post-Money Valuation (using SaaS multiples):
├─ Year 1 ARR: $939,316 (4 months of Run Rate)
├─ Typical SaaS multiple: 8-12x for pre-product-market fit
├─ Valuation range: $7.5M - $11.3M
└─ Dilution for $1.5M @ $10M valuation: 15% investor stake

Alternative (Comparable Companies):
├─ Logitech (logistics SaaS): 18x revenue multiple
├─ Rivigo (L2M platform): $500M valuation @ $100M revenue
├─ Industry range: 5-20x revenue (depending on growth)
└─ Conservative estimate for Georgensen at launch: 5-8x
```

### Potential Exit Scenarios (Year 3-5)

#### Scenario A: M&A (Most Likely)

```
Year 3 Revenue: $9M
Acquirer: Existing courier (FedEx, DHL, UPS, Aramex, Chewy2go)
Valuation multiple: 4-6x revenue (corporate acquisition discount)
Potential valuation: $36-54M
Investor return: 24-36x on $1.5M investment
Timeline: Year 3-4 (when product-market fit proven)
```

#### Scenario B: Strategic Partnership

```
Acquirer: E-commerce platform (Shopify, Amazon, WooCommerce)
Purpose: Add shipping functionality
Valuation: Lower multiple (2-3x) but strategic benefits
Potential valuation: $18-27M
Investor return: 12-18x
Benefits: Immediate customer base, market exposure
```

#### Scenario C: IPO (Aggressive Growth)

```
Requirement: $100M+ ARR by Year 7
Market conditions: Favorable tech IPO market
Valuation multiple: 8-12x revenue for growth companies
Potential valuation: $800M - $1.2B
Investor return: 533x - 800x (if original $667/share)
Timeline: Year 5-7 (pending growth milestones)
Probability: 10% (requires exceptional execution)
```

#### Scenario D: PE Recapitalization

```
Timing: Year 3-4 (when EBITDA > $1M)
Structure: PE firm buys majority, founder/team gets payout
Valuation: 8-12x EBITDA ($8-12M at Year 3 EBITDA of $1M)
Investor return: 5-8x on original $1.5M
Structure: Founders & early investors typically cash out 30-50%
Secondary proceeds: Can fuel further growth via debt/equity
Next exit: IPO or trade sale in Year 6-10
```

---

## KEY FINANCIAL METRICS & BENCHMARKS

### Unit Economics

```
Customer LTV (Lifetime Value):
├─ Average order value: $16.50
├─ Orders/customer (cohort): 10 orders
├─ Total revenue per customer: $165
├─ Platform margin (30%): $49.50
├─ Less CAC ($75): -$75
├─ Net LTV: -$25.50 (negative in Year 1!)
└─ By Year 2: +$20/customer (LTV > CAC)

LTV:CAC Ratio Target: 3:1 or higher
├─ Year 1: 0.66:1 (below target, acceptable for growth/acquisition)
├─ Year 2: 1.5:1 (approaching target)
└─ Year 3: 2.5:1 (healthy, can support higher CAC)

Customer Retention:
├─ Month 1: 100% (day 1)
├─ Month 3: 60% remain (40% churn)
├─ Month 6: 40% (additional 20% churn)
├─ Month 12: 15% (additional 25% churn)
├─ Annual cohort retention: 15% (typical for courier/shipping)
└─ Target improvement: 25% by Year 2 (better service)

Gross Margin:
├─ Per-order gross margin: 27.8% (after partner payout + payments)
├─ This is the contribution margin available for fixed costs
├─ Industry benchmark: 25-35% (we're at positive end)
└─ Path to 35%: Scale fixed cost advantages + reduced CAC
```

### Profitability Metrics

```
Break-Even Analysis:
├─ Fixed costs: $600K/year
├─ Contribution margin/order: $4.92
├─ Break-even orders: 122,000 orders/year
├─ Break-even monthly: ~10,000 orders
├─ Timeline to break-even: 15 months (Month in Q2 Year 2)

Payback Period:
├─ Initial investment: $1,500,000
├─ Monthly EBITDA (Year 2 average): $206,000
├─ Cumulative payback: 30 months (Month 30 = Sept year 3)
├─ Cash-on-cash return: 1.0x in 30 months (33% annual IRR)
└─ Improved with optimistic scenario (24 months breakeven)

CAGR (Compound Annual Growth Rate):
├─ Year 1-3 Revenue CAGR: 135%
│  (from $939K Year 1 to $8.9M Year 3)
├─ Year 1-3 Order CAGR: 126%
│  (from 202K to 1.8M orders)
└─ Exceeds typical SaaS CAGR benchmarks (50-100%)
```

---

## FINANCIAL RISKS & MITIGATION

### Risk: Rapid Competitive Pressure

```
Probability: High (large couriers digitizing)
Impact: Pricing pressure (-20%), customer churn (+30%)
Revenue impact: -$600K annually

Mitigation:
├─ Build brand loyalty early (exceptional service)
├─ Lock in enterprise customers (longer contracts)
├─ Differentiation: Tech + transparency (hard to replicate)
├─ Geographic focus (dominate one market before scaling)
└─ Strategic partnerships (with complementary businesses)

Financial reserve: Keep 3 months OPEX in cash ($150K)
```

### Risk: Partner Network Collapse

```
Probability: Medium (gig economy churn is high)
Impact: Cannot fulfill orders, customer churn
Revenue impact: Potential 50% order loss

Mitigation:
├─ Diversify partner base (no single partner > 5% of volume)
├─ Incentive programs (bonuses for low churn partners)
├─ Predictable pricing (attract quality long-term partners)
├─ Rapid onboarding (can scale network quickly)
└─ Backup arrangements (relationships with competing networks)

Financial reserve: Partner churn budget ($50K annually)
```

### Risk: Regulatory Changes

```
Probability: Low to Medium (labor, safety regulations)
Impact: Potential 10-30% cost increases, new compliance costs

Mitigation:
├─ Partner classification (ensure "independent contractor" status)
├─ Insurance requirements (carry comprehensive coverage)
├─ Compliance team (hire 1 person in Year 2)
├─ Lobbying (join industry associations)
└─ Flexibility (can adapt to classification changes if needed)

Financial reserve: Annually $50K for compliance/legal
```

---

## CONCLUSION

Georgensen Courier demonstrates **strong financial fundamentals** with a clear path to profitability and attractive returns:

✅ **Break-even in 15 months** (Q2 Year 2)
✅ **Positive EBITDA of $2.5M+ by Year 2** 
✅ **Scalable unit economics** (27.8% gross margin, expandable)
✅ **Attractive investor returns** (5x+ in 3-5 years)
✅ **Multiple exit opportunities** (M&A most likely Year 3-4 at $30-50M)

⚠️ **Key Dependencies:**
1. Execute product launch with < 10 bugs
2. Acquire first 1,000 customers profitably ($75 CAC)
3. Maintain 70% partner satisfaction
4. Keep order growth at 15%+ MoM Year 1

**Recommendation:** Fund the round. This is a high-growth, capital-efficient business with proven market demand and clear profitability path.

---

**Financial Model prepared:** February 10, 2026  
**Prepared by:** CFO Analysis Team  
**Next review:** Quarterly (May 10, 2026)
