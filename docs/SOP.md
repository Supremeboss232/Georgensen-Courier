# GEORJENSEN - Operations Standard Operating Procedure (SOP)

**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Status:** Active

---

## TABLE OF CONTENTS

1. [Order Intake](#1-order-intake)
2. [Pricing & Quotation](#2-pricing--quotation)
3. [Partner Assignment](#3-partner-assignment)
4. [Pickup & Delivery Tracking](#4-pickup--delivery-tracking)
5. [Proof of Delivery](#5-proof-of-delivery)
6. [Customer Support & Disputes](#6-customer-support--disputes)
7. [Settlement & Payments](#7-settlement--payments)
8. [International Courier (Phase 2)](#8-international-courier-phase-2)
9. [Record Keeping & Reporting](#9-record-keeping--reporting)
10. [Quality Standards](#10-quality-standards)

---

## 1. ORDER INTAKE

### Objective
Process customer delivery requests efficiently and accurately through multiple channels.

### Channels
- **Website:** "Get a Quote" form at www.georjensen.com/quote
- **WhatsApp Business:** Direct message to +1 (555) 123-4567
- **Email:** support@georjensen.com
- **Phone:** Available for corporate clients

### Procedure

#### Step 1: Receive & Log Request
1. Receive delivery request from customer
2. Log request immediately in Admin Dashboard with timestamp
3. Assign unique Tracking Number in format: `GEO-YYYY-XXXXXX`

#### Step 2: Verify Information
Confirm all required information is complete:

**Essential Information:**
- ✓ Pickup address (street, city, zip, country)
- ✓ Delivery address (street, city, zip, country)
- ✓ Package type & size
- ✓ Package weight (approximate)
- ✓ Package description
- ✓ Delivery speed preference (Express/Standard/Economy)
- ✓ Customer name & contact
- ✓ Email address
- ✓ Phone number

#### Step 3: Contact Customer
- Send confirmation email with:
  - Tracking number
  - Quote amount
  - Estimated delivery date
  - Payment instructions
- Include WhatsApp link for quick support

#### Step 4: Handle Incomplete Information
- If information is missing, contact customer immediately
- Maximum 2 hours to follow up with incomplete requests
- Do not proceed to next step without complete information

### Quality Checkpoints
- [ ] All required fields are filled
- [ ] Addresses are valid and complete
- [ ] Contact details are correct
- [ ] Confirmation email sent successfully

---

## 2. PRICING & QUOTATION

### Objective
Provide accurate, transparent pricing based on service parameters.

### Pricing Model

#### Base Fare (Service Fee)
- **Local Courier:** $5.00
- **Inter-City Courier:** $15.00
- **International Courier (Phase 2):** $50.00

#### Distance Charge (per km)
- **Local:** $0.50/km (average 5 km)
- **Inter-City:** $0.30/km (average 150 km)
- **International:** $0.10/km estimate (flat rate for aggregators)

#### Weight Charge (per kg)
- **Local:** $2.00/kg
- **Inter-City:** $1.50/kg
- **International:** $3.00/kg

#### Speed Premium (Multiplier)
- **Express (Same Day):** 1.5x (50% premium)
- **Standard (Next Day):** 1.0x (base rate)
- **Economy (48 Hours):** 0.8x (20% discount)

#### Package Type Multiplier
- **Document:** 0.5x
- **Small Parcel:** 1.0x
- **Medium Box:** 1.5x
- **Large Package:** 2.5x

#### Insurance (Optional)
- **Cost:** 5% of estimated package value
- **Value Estimation:** $50 per kg

### Quotation Process

#### Step 1: Calculate Quote
```
Quote = (Base Fare + Distance Charge + Weight Charge) × Speed Premium × Package Type + Insurance (if selected)
```

#### Step 2: Validate Quote
- Confirm with customer in writing
- Include itemized breakdown
- Show estimated delivery date

#### Step 3: Quote Acceptance
- Customer must confirm and pay (online or invoice)
- Quote is valid for 24 hours
- No delivery proceeds without payment confirmation

### Payment Methods
- Credit/Debit Card (Stripe)
- Bank Transfer
- Digital Wallets (PayPal, Apple Pay, Google Pay)
- Corporate Invoice (monthly billing)

### Quality Checkpoints
- [ ] Quote is calculated correctly
- [ ] Itemized breakdown provided
- [ ] Quote confirmed with customer
- [ ] Payment received before proceeding

---

## 3. PARTNER ASSIGNMENT

### Objective
Efficiently match deliveries with qualified, available couriers to ensure reliability.

### Partner Eligibility
**Couriers must meet:**
- ✓ Valid ID & background check
- ✓ Minimum 4.5/5 reliability rating
- ✓ Vehicle ownership/lease proof
- ✓ Insurance coverage
- ✓ GPS tracking device operational
- ✓ Mobile app access

### Assignment Criteria
1. **Proximity:** Nearest available partner to pickup location
2. **Capacity:** Partner has vehicle space for package
3. **Reliability:** Minimum 95% on-time delivery rate
4. **Service Type:** Partner certified for service type (local/intercity)
5. **Availability:** Partner currently active and accepting orders

### Assignment Procedure

#### Step 1: Open Admin Dashboard
- Navigate to "Unassigned Deliveries"
- Filter by service type and location

#### Step 2: Select Best Partner
- Identify 2-3 nearest qualified partners
- Check their current load
- Review past 30-day performance

#### Step 3: Send Assignment
- Send to partner's app with:
  - Tracking number
  - Pickup address & time window
  - Delivery address
  - Package details & weight
  - Special instructions
  - Agreed payout ($X per delivery)
  - Contact number for customer

#### Step 4: Confirm Acceptance
- Partner must confirm within 15 minutes
- If no confirmation, reassign to another partner
- Document partner response time

#### Step 5: Failed Reassignment
- If no partner accepts within 45 minutes, contact customer
- Offer alternative:
  - New time window
  - Full refund
  - Rescheduling

### Payment to Partners
- **Local:** $3-8 per delivery (based on distance)
- **Inter-City:** $10-25 per delivery (based on distance)
- **Special Handling:** +20% premium (fragile, urgent)

### Quality Checkpoints
- [ ] Partner meets all eligibility criteria
- [ ] Partner confirms assignment
- [ ] All delivery details transmitted clearly
- [ ] Partner assigned within 30 minutes of payment

---

## 4. PICKUP & DELIVERY TRACKING

### Objective
Maintain real-time visibility of all shipments and keep customers informed.

### Status Updates

#### Order Received
- ✓ Triggered: When payment is confirmed
- ✓ Auto-notify: Customer receives email confirmation
- ✓ Dashboard: Status shows "Order Received"

#### Picked Up
- ✓ Triggered: Partner updates app with GPS location + photo
- ✓ Auto-notify: Customer receives SMS/WhatsApp notification
- ✓ Dashboard: Delivery status updates to "Picked Up"

#### In Transit
- ✓ Triggered: Partner begins delivery journey
- ✓ Auto-notify: Customer receives "Out for delivery" notification
- ✓ Dashboard: GPS updates every 5 minutes (if available)

#### Delivered
- ✓ Triggered: Partner uploads proof of delivery (photo/signature)
- ✓ Auto-notify: Customer receives "Delivered" confirmation
- ✓ Dashboard: Delivery marked complete

### Monitoring Process

#### Real-Time Monitoring
1. **Dashboard Check:** Admin reviews "Active Deliveries" every 4 hours
2. **Issue Detection:** Flag deliveries with:
   - No movement for >30 minutes
   - Partner offline >20 minutes
   - Customer called about location

#### Delay Management
- If delay detected:
  - Contact partner immediately (WhatsApp call)
  - Update customer with ETA
  - Log reason for delay
  - Monitor for further updates

#### Customer Notification
- Standard updates: Email
- Urgent updates: SMS + WhatsApp
- Failed deliveries: Immediate phone call

### Quality Checkpoints
- [ ] Status updates are accurate & timely
- [ ] Customer receives 3+ updates during delivery
- [ ] No tracking gaps exceed 30 minutes
- [ ] Admin notified of delays within 15 minutes

---

## 5. PROOF OF DELIVERY

### Objective
Document successful delivery with photographic or signature evidence.

### Requirements

All deliveries MUST include:

#### Option A: Photo Proof
- ✓ Photo of package at delivery location
- ✓ Photo showing delivery address/house number
- ✓ Photo with recipient (if possible)
- ✓ Timestamp embedded in photo
- ✓ GPS coordinates logged

#### Option B: Signature Proof
- ✓ Recipient signature on digital form
- ✓ Recipient name (printed clearly)
- ✓ Recipient ID verification (optional for high-value)
- ✓ Timestamp of signature
- ✓ GPS coordinates

#### Option C: Video Proof (High-Value Items)
- ✓ 10-15 second video showing package & address
- ✓ Video timestamp and GPS
- ✓ Partner identification in video
- ✓ Recipient visible in video

### Process

#### Step 1: Partner Uploads Proof
- Via Georjensen mobile app
- Within 10 minutes of delivery
- Proof includes all required elements

#### Step 2: Admin Verification
- Review within 2 hours
- Check:
  - Proof authenticity
  - GPS matches delivery address
  - All required elements present
  - No discrepancies

#### Step 3: Approve/Reject
- **Approve:** Mark delivery complete, release customer confirmation
- **Reject:** Contact partner, request re-upload or clarification

#### Step 4: Store Proof
- Save to cloud storage (encrypted)
- Link to delivery record
- Accessible for 2 years (compliance)

### Quality Checkpoints
- [ ] Proof received within 10 minutes of delivery
- [ ] All elements of proof present
- [ ] Admin reviews and approves within 2 hours
- [ ] Customer receives final confirmation

---

## 6. CUSTOMER SUPPORT & DISPUTES

### Objective
Resolve customer issues quickly while maintaining service quality.

### Common Issues

#### A. Late Delivery

**Threshold:** >30 minutes beyond guaranteed time

**Process:**
1. Contact customer within 15 minutes of estimated delivery time
2. Provide updated ETA
3. If further delay >15 minutes:
   - Offer 10% refund OR
   - Rescheduled free delivery
4. Document reason (traffic, address issue, etc.)

**Resolution Options:**
- Partial refund (10-20%)
- Free rescheduled delivery
- Priority next delivery (free)

#### B. Damaged/Lost Package

**If Package Damaged:**
1. Request photo evidence from customer
2. Request photo from partner (condition at delivery)
3. Review claim within 24 hours
4. Offer:
   - Full refund of shipping + compensation
   - Resend package (if customer requests)
5. Investigate partner (check history)
6. If pattern: Deactivate partner after 2 incidents

**If Package Lost:**
1. Contact partner immediately
2. Verify delivery was NOT completed
3. Search for package (retrace route)
4. If not found within 4 hours:
   - Full refund to customer
   - File insurance claim (if insured)
5. Investigate partner: Possible suspension

#### C. Address Not Found

**Process:**
1. Confirm address with customer
2. Request partner to contact customer for clarification
3. If address invalid:
   - Offer refund, OR
   - Redeliver to corrected address (free)
4. Document issue (customer error vs. system error)

#### D. Customer Not Available

**Process:**
1. Partner attempts delivery (documented)
2. Leave safe place notice if available
3. Reschedule delivery within 24 hours
4. If customer unavailable 2x:
   - Contact customer for arrangement
   - Hold package for 5 days max
   - After 5 days: Offer full refund

### Complaint Recording

**All complaints must be logged with:**
- Tracking number
- Customer name & contact
- Date & time of complaint
- Issue description
- Resolution offered
- Date resolved

### Response Times

| Issue Type | Response Target | Resolution Target |
|-----------|-----------------|------------------|
| General Inquiry | 2 hours | N/A |
| Delay | 15 minutes | 2 hours |
| Damage | 4 hours | 24 hours |
| Loss | 4 hours | 24 hours |
| Quality Complaint | 1 hour | 24 hours |

### Quality Checkpoints
- [ ] Issue logged within 30 minutes
- [ ] Customer contacted within response target
- [ ] Resolution offered & documented
- [ ] Follow-up completed within 48 hours

---

## 7. SETTLEMENT & PAYMENTS

### Objective
Process accurate, timely payments to partner couriers.

### Payment Schedule

**Standard:** Bi-weekly (every 2 weeks)  
**Premium Partners:** Weekly (4.8+ rating)  
**At-Risk Partners:** Monthly (under review)

### Settlement Process

#### Step 1: Compile Deliveries (Every Monday)
1. Pull all completed deliveries from past 2 weeks
2. Verify POD (proof of delivery) for each
3. Filter deliveries by partner
4. Calculate subtotal per partner

#### Step 2: Calculate Payouts

**Formula:**
```
Partner Payout = (Agreed Rate × Number of Completed Deliveries) - Penalties - Service Fee
```

**Deductions:**
- Late delivery: -10% of delivery fee
- Customer complaint: -$5-20 (depending on severity)
- Failed delivery: $0 (no payment)
- Damage claim: -$10-50 (investigation determines)

#### Step 3: Generate Reports
- Individual payment summary per partner
- Invoice with:
  - Delivery list
  - Fees breakdown
  - Deductions (if any)
  - Net payout
  - Payment date
  - Reference number

#### Step 4: Process Payments

**Payment Methods:**
- Bank transfer (primary)
- Digital wallet (Stripe, PayPal)
- Check (if requested)

**Record:**
- Transaction ID
- Timestamp
- Confirmation sent to partner

#### Step 5: Partner Confirmation
- Partner receives payment confirmation
- Partner signs off on settlement
- Archive invoice (7-year retention)

### Quality Checkpoints
- [ ] All POD verified before payment
- [ ] No payment without POD approval
- [ ] Settlement calculated accurately
- [ ] Payment processed on scheduled date
- [ ] Audit trail complete

---

## 8. INTERNATIONAL COURIER (PHASE 2)

### Objective
Provide seamless global shipping through partner aggregators (DHL, FedEx, UPS).

### Launching in Q2 2026

### Process Overview

#### Step 1: Customer Submits International Order
- Website form or WhatsApp
- Destination country (200+ countries supported)
- Package details & weight
- Declared value

#### Step 2: Rate Check
- Admin checks rates with DHL/FedEx/UPS
- Compare delivery times & pricing
- Present best options to customer

#### Step 3: Customs Documentation
- Customer provides/confirms:
  - Shipper details
  - Receiver details
  - Item description (accurate)
  - HS Code (if applicable)
  - Declared value
  - Commercial invoice (if goods)

#### Step 4: Booking
- Admin books shipment with selected aggregator
- Receive tracking number from aggregator
- Create Georjensen tracking record

#### Step 5: Pickup
- Aggregator schedules pickup OR
- Customer delivers to Georjensen collection point
- POD collected at pickup

#### Step 6: Ongoing Tracking
- Georjensen tracks via aggregator
- Update customer with status changes
- Manage clearance/customs issues

#### Step 7: Delivery
- Final delivery by aggregator
- Collect POD
- Confirm with customer

### Premium International Features
- One invoice (Georjensen interface, not 3+ providers)
- Unified tracking dashboard
- 24/7 support for customs issues
- Insurance included for declared value >$500
- White-glove corporate support

---

## 9. RECORD KEEPING & REPORTING

### Objective
Maintain accurate records for compliance, analysis, and improvement.

### Daily Records

**Admin Dashboard captures:**
- Deliveries completed
- Pending deliveries
- Failed deliveries
- Customer complaints
- Partner issues

### Weekly Report

**Every Monday, compile:**

| Metric | Target |
|--------|--------|
| Total Deliveries | Track trend |
| On-Time Rate | >95% |
| Customer Satisfaction | >4.7/5 |
| Partner Avg Rating | >4.8/5 |
| Complaints Resolved | 100% |
| Avg Resolution Time | <24 hrs |
| Revenue | $ |
| Costs | $ |
| Profit Margin | >35% |

**Format:** Excel sheet, email to management

### Monthly Report

**1st of every month, comprehensive analysis:**

1. **Delivery Metrics**
   - Total deliveries by service type
   - Average delivery time
   - On-time rate by service
   - Cancellation rate

2. **Financial Metrics**
   - Revenue breakdown by service
   - Cost breakdown (partners, operations)
   - Profit margin
   - Average order value

3. **Quality Metrics**
   - Customer satisfaction score
   - Complaint categories
   - Partner performance ranking
   - Issue resolution rate

4. **Operational Metrics**
   - Peak delivery times
   - Service type distribution
   - Geographic coverage
   - Growth trends

5. **Issues & Action Items**
   - Problems identified
   - Root cause analysis
   - Corrective actions
   - Timeline for resolution

**Distribution:** Stakeholders, investors, management

### Record Retention

| Record Type | Retention Period |
|------------|-----------------|
| Delivery Records | 7 years |
| Payment Records | 7 years |
| Customer Complaints | 2 years |
| Proof of Delivery | 2 years |
| Partner Agreements | 5 years |
| Financial Records | 7 years |
| Marketing/Analytics | 3 years |

### Data Security
- All records encrypted (AES-256)
- Cloud backup (daily)
- Access logs maintained
- GDPR compliant

---

## 10. QUALITY STANDARDS

### Service Level Agreements (SLAs)

#### Local Courier
- **Order Processing:** <1 hour
- **Partner Assignment:** <30 minutes
- **Delivery Time:** 4-24 hours (based on service)
- **On-Time Rate:** >98%
- **Customer Satisfaction:** >4.8/5

#### Inter-City Courier
- **Order Processing:** <2 hours
- **Partner Assignment:** <1 hour
- **Delivery Time:** 1-2 business days
- **On-Time Rate:** >95%
- **Customer Satisfaction:** >4.7/5

#### Response Times
- **Customer Inquiry:** <2 hours
- **Complaint:** <15 minutes (urgent), <4 hours (standard)
- **Issue Resolution:** <24 hours

### Quality Metrics

**Monthly Targets:**
- ✓ On-time delivery: >95%
- ✓ Customer satisfaction: >4.7/5
- ✓ Complaint rate: <2% of deliveries
- ✓ Damage rate: <0.5% of deliveries
- ✓ Partner reliability: >95% of partners
- ✓ Payment accuracy: 100%

### Continuous Improvement

**Monthly Review:**
1. Identify low-performing areas
2. Root cause analysis
3. Develop corrective action
4. Implement improvement
5. Track effectiveness

**Quarterly Audit:**
- Compliance check
- SOP review & updates
- Staff training needs
- Technology upgrades

---

## APPENDIX A: USEFUL CONTACTS

**Internal:**
- Admin Lead: support@georjensen.com
- Finance: finance@georjensen.com
- Operations: ops@georjensen.com

**Partner Support:**
- WhatsApp: +1 (555) 123-4567
- Email: partners@georjensen.com

**Customer Support:**
- WhatsApp: +1 (555) 123-4567
- Email: support@georjensen.com
- Phone: +1 (555) 000-0000

**External Aggregators (Phase 2):**
- DHL: [contact info]
- FedEx: [contact info]
- UPS: [contact info]

---

**Document Approved By:** [Signature]  
**Date:** February 4, 2026  
**Next Review:** May 4, 2026

---

*This SOP is a living document. Updates will be communicated to all staff within 48 hours.*
