"""Regenerate samples/example-*.xml.

The element names follow the public ISO 20022 and TWIST schemas. Every value is invented.
Usage: python samples/make_samples.py samples
"""
from decimal import Decimal

def amt(tag, v, ccy, sgn='true'):
    return f'<{tag}><Amt Ccy="{ccy}">{v:.2f}</Amt><Sgn>{sgn}</Sgn></{tag}>'

SERVICES = [
    ("PAY-DOM-OUT", "Domestic payment, outbound", 412, Decimal("0.35"), "UPRC", "true"),
    ("PAY-INT-OUT", "International payment, outbound", 96, Decimal("11.50"), "UPRC", "true"),
    ("ACC-MAINT", "Account maintenance, monthly", 1, Decimal("45.00"), "FCHG", "true"),
    ("REB-VOL", "Volume rebate", 1, Decimal("60.00"), "FCHG", "false"),
]

def camt():
    out = []
    p = out.append
    p('<?xml version="1.0" encoding="UTF-8"?>')
    p('<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.086.001.01">')
    p('  <BkSvcsBllgStmt>')
    p('    <RptHdr><RptId>000000000001</RptId></RptHdr>')
    p('    <BllgStmtGrp>')
    p('      <GrpId>Group 1 of 1</GrpId>')
    p('      <Sndr><Nm>Example Bank plc</Nm><LglNm>Example Bank plc</LglNm>'
      '<PstlAdr><AdrTp>BIZZ</AdrTp><AdrLine>1 Example Street</AdrLine><AdrLine>Sampletown AB1 2CD</AdrLine><AdrLine>United Kingdom</AdrLine></PstlAdr>'
      '<Id><OrgId><AnyBIC>EXAMGB2LXXX</AnyBIC></OrgId></Id><CtryOfRes>GB</CtryOfRes></Sndr>')
    p('      <Rcvr><Nm>Example Corp Ltd</Nm>'
      '<PstlAdr><AdrTp>BIZZ</AdrTp><AdrLine>99 Sample Road</AdrLine><AdrLine>Testville XY9 8ZZ</AdrLine><AdrLine>United Kingdom</AdrLine></PstlAdr>'
      '<Id><OrgId><Othr><Id>CUSTOMER-0001</Id></Othr></OrgId></Id><CtryOfRes>GB</CtryOfRes></Rcvr>')
    p('      <BllgStmt>')
    p('        <StmtId>STM-EXAMPLE-0001</StmtId>')
    p('        <FrToDt><FrDt>2026-10-01</FrDt><ToDt>2026-10-31</ToDt></FrToDt>')
    p('        <CreDtTm>2026-11-02T06:15:00Z</CreDtTm>')
    p('        <Sts>ORGN</Sts>')
    p('        <AcctChrtcs>')
    p('          <AcctLvl>SUMM</AcctLvl>')
    p('          <CshAcct><Id><IBAN>GB00EXAM00000000000001</IBAN></Id><Ccy>GBP</Ccy><Nm>Example operating account</Nm></CshAcct>')
    p('          <AcctSvcr><FinInstnId>EXAMGB2LXXX</FinInstnId><BrnchId><Nm>Sampletown branch</Nm>'
      '<PstlAdr><AdrTp>BIZZ</AdrTp><AdrLine>1 Example Street</AdrLine></PstlAdr></BrnchId></AcctSvcr>')
    p('          <CompstnMtd>DDBT</CompstnMtd>')
    p('          <DbtAcct><IBAN>GB00EXAM00000000000001</IBAN></DbtAcct>')
    p('          <DelydDbtDt>2026-11-15</DelydDbtDt>')
    p('          <SttlmAdvc>false</SttlmAdvc>')
    p('          <AcctBalCcyCd>GBP</AcctBalCcyCd><SttlmCcyCd>GBP</SttlmCcyCd><HstCcyCd>GBP</HstCcyCd>')
    p('          <Tax><ClctnMtd>MTDA</ClctnMtd><Rgn>GB</Rgn></Tax>')
    p('          <AcctSvcrCtct><Nm>Billing team</Nm><EmailAdr>billing@example.com</EmailAdr></AcctSvcrCtct>')
    p('        </AcctChrtcs>')
    for code, v in (("AVGB", "250000.00"), ("ACRT", "0.0125")):
        p(f'        <Compstn><Tp><Cd>{code}</Cd></Tp><Val><Amt Ccy="GBP">{v}</Amt><Sgn>true</Sgn></Val><CcyTp>STLM</CcyTp></Compstn>')
    tot_chrg = tot_tax = Decimal(0)
    for sid, desc, vol, price, mtd, sgn in SERVICES:
        charge = (price * vol).quantize(Decimal("0.01"))
        tax = (charge * Decimal("0.20")).quantize(Decimal("0.01"))
        total = charge + tax
        s = lambda tag, v: amt(tag, v, "GBP", sgn)
        p('        <Svc>')
        p(f'          <SvcDtl><BkSvc><Id>{sid}</Id><Desc>{desc}</Desc><CmonCd><Issr>TWIST</Issr><Id>{sid[:3]}</Id></CmonCd></BkSvc><Vol>{vol}</Vol></SvcDtl>')
        p(f'          <Pric><Ccy>GBP</Ccy><UnitPric><Amt Ccy="GBP">{price:.2f}</Amt><Sgn>true</Sgn></UnitPric><Mtd>{mtd}</Mtd></Pric>')
        p('          <PmtMtd>FLAT</PmtMtd>')
        p('          ' + s('OrgnlChrgPric', charge))
        p('          ' + s('OrgnlChrgSttlmAmt', charge))
        p('          <TaxDsgnt><Cd>TAXD</Cd><Rgn>GB</Rgn><TaxRsn><Cd>STND</Cd><Expltn>Standard rate</Expltn></TaxRsn></TaxDsgnt>')
        p('          <TaxClctn><MtdA>')
        p('            ' + s('SvcChrgHstAmt', charge))
        p(f'            <SvcTax>{amt("HstAmt", tax, "GBP", sgn)}{amt("PricgAmt", tax, "GBP", sgn)}</SvcTax>')
        p(f'            <TtlChrg>{amt("HstAmt", total, "GBP", sgn)}{amt("SttlmAmt", total, "GBP", sgn)}{amt("PricgAmt", total, "GBP", sgn)}</TtlChrg>')
        p(f'            <TaxId><Nb>1</Nb><Desc>VAT</Desc><Rate>20.00</Rate>{amt("HstAmt", tax, "GBP", sgn)}{amt("PricgAmt", tax, "GBP", sgn)}</TaxId>')
        p('          </MtdA></TaxClctn>')
        p('        </Svc>')
        sign = -1 if sgn == "false" else 1
        tot_chrg += sign * charge
        tot_tax += sign * tax
    p('        <TaxRgn>')
    p('          <RgnNb>1</RgnNb><RgnNm>United Kingdom</RgnNm><CstmrTaxId>GB000000000</CstmrTaxId><PtDt>2026-10-31</PtDt>')
    p('          <SndgFI><VATRegnNb>GB111111111</VATRegnNb></SndgFI><InvcNb>INV-EXAMPLE-0001</InvcNb>')
    p('          ' + amt('SttlmAmt', tot_chrg + tot_tax, 'GBP'))
    p('          ' + amt('TaxDueToRgn', tot_tax, 'GBP'))
    p('        </TaxRgn>')
    p('      </BllgStmt>')
    p('    </BllgStmtGrp>')
    p('  </BkSvcsBllgStmt>')
    p('</Document>')
    return '\n'.join(out) + '\n'

def twist():
    ns = 'xmlns="http://www.twiststandards.org/3.1/ElectronicBilling" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ElectronicBillingMsg"'
    L = []
    p = L.append
    p('<?xml version="1.0" encoding="UTF-8"?>')
    p(f'<Twist {ns}>')
    p('  <header xsi:type="ResponseMessageHeader"><messageId>EXAMPLE-MSG-0001</messageId><inReplyTo>EXAMPLE-REQ-0001</inReplyTo>'
      '<sentBy id="_EXAMPLEBANK_"><typedPartyId><partyId>EXAMPLE</partyId><partyIdType>EXAMPLE</partyIdType></typedPartyId></sentBy>'
      '<creationTimestamp>2026-11-03T05:40:00.000Z</creationTimestamp></header>')
    p('  <electronicStatement>')
    p('    <statementHeader>')
    p('      <stmtSender><orgId><orgIdType>SW</orgIdType><orgIdNum>EXAMGB2L</orgIdNum></orgId><name>Example Bank plc</name><legalName>Example Bank plc</legalName>'
      '<contactInfo><postAddress><addressLine>1 Example Street</addressLine><city>Sampletown</city><countrySubDivision><name>Exampleshire</name></countrySubDivision><country>GB</country><postCode>AB1 2CD</postCode></postAddress></contactInfo></stmtSender>')
    p('      <stmtReceiver><name>Example Corp Ltd</name><legalName>Example Corp Ltd</legalName>'
      '<contactInfo><postAddress><city>Testville</city><country>GB</country></postAddress></contactInfo></stmtReceiver>')
    p('    </statementHeader>')
    p('    <statement>')
    p('      <account><accountLevel>SUMM</accountLevel><bban>EXAM00000001</bban><iban>GB00EXAM00000000000001</iban>'
      '<statementStartDate>2026-10-01</statementStartDate><statementEndDate>2026-10-31</statementEndDate><statementProductionDate>2026-11-02</statementProductionDate>'
      '<statementStatus>ORGN</statementStatus><accountName>Example operating account</accountName><compensationMethod>DDBT</compensationMethod>'
      '<debitAccount>EXAM00000001</debitAccount><delayedDebitDate>2026-11-15</delayedDebitDate><settlementAdvice>false</settlementAdvice>'
      '<accountBalanceCurrencyCode>GBP</accountBalanceCurrencyCode><settlementCurrencyCode>GBP</settlementCurrencyCode><taxRegionCode>GB</taxRegionCode><taxRegionResident>true</taxRegionResident></account>')
    p('      <currencyTranslation><originalCurrency>USD</originalCurrency><targetCurrency>GBP</targetCurrency><translationValue>0.7900</translationValue><basis>MNTH</basis></currencyTranslation>')
    for ident, v in (("AVGLEDGER", "250000.00"), ("AVGCOLLECTED", "245000.00")):
        p(f'      <balance><balanceIdentifier>{ident}</balanceIdentifier><balanceValue><amount>{v}</amount><currency>GBP</currency></balanceValue></balance>')
    for ident, v in (("ECR", "0.0125"), ("EARNINGS", "260.42")):
        p(f'      <compensation><compensationIdentifier>{ident}</compensationIdentifier><compensationValue><amount>{v}</amount><currency>GBP</currency></compensationValue></compensation>')
    for n, (sid, desc, vol, price, mtd, sgn) in enumerate(SERVICES, 1):
        charge = (price * vol).quantize(Decimal("0.01"))
        if sgn == "false":
            charge = -charge
        p('      <service>'
          f'<bankServiceID>{sid}</bankServiceID><subServiceCode>{n:03d}</subServiceCode><commonCode>{sid[:3]}</commonCode>'
          f'<serviceDescription>{desc}</serviceDescription><serviceType>ACCOUNT</serviceType><volume>{vol}</volume><pricingCurrencyCode>GBP</pricingCurrencyCode>'
          f'<unitPrice><amount>{price:.2f}</amount><currency>GBP</currency></unitPrice><priceMethod>{mtd}</priceMethod><paymentMethod>FLAT</paymentMethod>'
          f'<originalChargePrice><amount>{charge:.2f}</amount><currency>GBP</currency></originalChargePrice>'
          f'<originalChargeSettlement><amount>{charge:.2f}</amount><currency>GBP</currency></originalChargeSettlement>'
          '<taxDesignation>TAXD</taxDesignation><serviceTaxRegion>GB</serviceTaxRegion>'
          '<taxIdentificationGroup><taxIdentifierNumber>1</taxIdentifierNumber><taxIdentifierRate>20.00</taxIdentifierRate></taxIdentificationGroup>'
          '</service>')
    p('    </statement>')
    p('  </electronicStatement>')
    p('</Twist>')
    return '\n'.join(L) + '\n'

if __name__ == '__main__':
    import sys
    d = sys.argv[1]
    open(f'{d}/example-camt086.xml', 'w', encoding='utf-8').write(camt())
    open(f'{d}/example-twist.xml', 'w', encoding='utf-8').write(twist())
