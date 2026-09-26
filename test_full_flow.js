const http = require('http');

function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: data, headers: res.headers }));
    }).on('error', reject);
  });
}

async function runTests() {
  console.log('================================================================');
  console.log('VOICESHIELD AI: COMPLETE END-TO-END SCENARIO VERIFICATION SUITE');
  console.log('================================================================');
  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log('  [PASS]', message);
      passed++;
    } else {
      console.error('  [FAIL]', message);
      failed++;
    }
  }

  try {
    // 1. Backend Scenarios List
    console.log('\n--- 1. Catalog Verification (GET /api/v1/demo/scenarios) ---');
    const scenariosRes = await get('http://127.0.0.1:8000/api/v1/demo/scenarios');
    assert(scenariosRes.status === 200, 'Scenario catalog returns 200 OK');
    const scenarios = JSON.parse(scenariosRes.body);
    assert(scenarios.length === 6, `Catalog contains exactly 6 scenarios (got ${scenarios.length})`);

    const expectedScenarios = [
      { id: 'bank-otp-scam', score: 94, level: 'HIGH', caller: 'HDFC Bank Security Desk', hasWarning: true },
      { id: 'technical-remote-access', score: 86, level: 'HIGH', caller: 'Amazon Refund Helpdesk', hasWarning: true },
      { id: 'digital-arrest', score: 92, level: 'HIGH', caller: 'Cyber Crime Branch Delhi', hasWarning: true },
      { id: 'lottery-scam', score: 78, level: 'HIGH', caller: 'KBC Lottery Department', hasWarning: true },
      { id: 'legitimate-bank-call', score: 8, level: 'LOW', caller: 'ICICI Bank Card Protection', hasWarning: false },
      { id: 'poor-quality-benign', score: 14, level: 'LOW', caller: 'Colleague / Arun', hasWarning: false },
    ];

    for (const exp of expectedScenarios) {
      const match = scenarios.find(s => s.id === exp.id);
      assert(!!match, `Found scenario '${exp.id}'`);
      if (match) {
        assert(match.expected_risk_score === exp.score, `'${exp.id}' has risk score ${exp.score}/100`);
        assert(match.expected_risk_level === exp.level, `'${exp.id}' has risk level ${exp.level}`);
        assert(match.caller_claimed === exp.caller, `'${exp.id}' claimed caller is '${exp.caller}'`);
        assert((match.warning_actions.length > 0) === exp.hasWarning, `'${exp.id}' warning actions count conforms (hasWarning=${exp.hasWarning})`);
      }
    }

    // 2. Exact Forensic Analysis Endpoint for All 6 Scenarios
    console.log('\n--- 2. Forensic Analysis & Evidence Verification (GET /api/v1/demo/scenarios/{id}/analysis) ---');
    for (const exp of expectedScenarios) {
      const anlRes = await get(`http://127.0.0.1:8000/api/v1/demo/scenarios/${exp.id}/analysis`);
      assert(anlRes.status === 200, `Scenario '${exp.id}' analysis returns 200 OK`);
      const anl = JSON.parse(anlRes.body);
      assert(anl.analysis_id === `DEMO-${exp.id}`, `Analysis ID matches 'DEMO-${exp.id}'`);
      assert(anl.risk.score === exp.score, `Analysis risk score is ${exp.score}`);
      assert(anl.is_demo_data === true, `Analysis flagged is_demo_data = true`);
      assert(typeof anl.voice.spoof_probability === 'number', `Voice spoof probability present (${anl.voice.spoof_probability})`);
      assert(typeof anl.speaker.similarity === 'number', `Speaker similarity present (${anl.speaker.similarity})`);
      assert(typeof anl.audio.quality_score === 'number', `Audio quality score present (${anl.audio.quality_score})`);

      if (exp.id === 'legitimate-bank-call') {
        assert(anl.risk.decision === 'BENIGN', 'Legitimate call decision is BENIGN');
        assert(anl.fraud_signals.length === 0, 'Legitimate call has 0 fraud signals');
      } else if (exp.id === 'poor-quality-benign') {
        assert(anl.risk.decision === 'BENIGN', 'Poor quality benign call decision is BENIGN');
        assert(anl.fraud_signals.length === 0, 'Poor quality call has 0 fraud signals');
        assert(anl.audio.quality_level === 'POOR', 'Audio quality correctly classified as POOR');
      } else {
        assert(anl.fraud_signals.length > 0, `Scam scenario '${exp.id}' detected ${anl.fraud_signals.length} fraud signals`);
      }
    }

    // 3. Frontend Pages Verification
    console.log('\n--- 3. Frontend Web Architecture Verification (localhost:3000) ---');
    const demoPage = await get('http://127.0.0.1:3000/demo');
    assert(demoPage.status === 200, 'GET /demo page loads (200 OK)');
    assert(demoPage.body.includes('live?scenario='), 'GET /demo has scenario deep-links');

    for (const exp of expectedScenarios) {
      const livePage = await get(`http://127.0.0.1:3000/live?scenario=${exp.id}`);
      assert(livePage.status === 200, `GET /live?scenario=${exp.id} loads (200 OK)`);
      assert(livePage.body.includes('Live Inbound Call Inspection'), `GET /live?scenario=${exp.id} renders live Telephony page`);

      const resPage = await get(`http://127.0.0.1:3000/result?scenario=${exp.id}`);
      assert(resPage.status === 200, `GET /result?scenario=${exp.id} loads (200 OK)`);
    }

    console.log(`\n================================================================`);
    console.log(`SUMMARY: ${passed} assertions passed, ${failed} failed.`);
    console.log(`================================================================\n`);

    if (failed > 0) process.exit(1);
  } catch (err) {
    console.error('Fatal test error:', err);
    process.exit(1);
  }
}

runTests();
