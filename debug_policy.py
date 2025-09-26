from stillme_core.middleware.reflex_policy import ReflexPolicy

p = ReflexPolicy('balanced')
scores = {'pattern_score': 0.9, 'context_score': 0.7, 'history_score': 0.5, 'abuse_score': 0.0}

print('Scores:', scores)
print('Weights:', p.weights)

total = 0.0
for score_type, weight in p.weights.items():
    score_value = scores.get(score_type, 0.0) or 0.0
    contrib = score_value * weight
    print(f'{score_type}: {score_value} * {weight} = {contrib}')
    total += contrib

print('Total:', total)
print('Abuse penalty:', scores.get('abuse_score', 0.0) or 0.0)
final = max(0.0, total - (scores.get('abuse_score', 0.0) or 0.0))
print('Final:', final)
print('Threshold:', p.thresholds['balanced']['allow_reflex'])
print('Allow:', final >= p.thresholds['balanced']['allow_reflex'])

# Test actual decide method
decision, confidence = p.decide(scores)
print('Actual decision:', decision, confidence)
