"""
Trading Signal Generation
==========================
Practical example: Generate actionable trading signals.

Use Case: Trader needs precise buy/sell recommendations
Quality Focus: Accuracy, precision, actionable insights
"""


from coinbase.patterns.pattern_dictionary import PatternDictionary, PatternType
from coinbase.security.privacy_vault import PrivacyVault
from coinbase.signals.trading_compass import TradingCompass
from coinbase.verification.verification_scale import VerificationScale


def generate_trading_signals(asset_symbol: str, current_price: float):
    """
    Generate precise trading signals for an asset.

    Demonstrates: Compass (signals), Scale (verification), Dictionary (patterns), Vault (security)
    """
    print("=" * 60)
    print(f"Trading Signal Generation: {asset_symbol}")
    print("=" * 60)
    print()

    # Initialize components
    compass = TradingCompass()
    scale = VerificationScale()
    dictionary = PatternDictionary()
    vault = PrivacyVault()

    # Step 1: Verify price
    print("Step 1: Price Verification")
    print("-" * 40)
    verification = scale.weigh_sources(asset_symbol, current_price)

    if verification.verified:
        print(f"✓ Price verified: ${verification.consensus:,.2f}")
        print(f"  Sources: {verification.sources_checked}/{verification.sources_verified}")
    else:
        print("⚠ Price verification failed")
        print(f"  Consensus: ${verification.consensus:,.2f}")
        if verification.anomalies:
            print("  Anomalies:")
            for anomaly in verification.anomalies:
                print(f"    - {anomaly}")
    print()

    # Step 2: Detect patterns
    print("Step 2: Pattern Detection")
    print("-" * 40)

    # Simulate pattern detection
    price_spike = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.08)
    volume_anomaly = dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.5)
    sentiment_shift = dictionary.recognize(PatternType.SENTIMENT_SHIFT, value=0.6)

    print(f"Price Spike: {'DETECTED' if price_spike.detected else 'None'}")
    print(f"Volume Anomaly: {'DETECTED' if volume_anomaly.detected else 'None'}")
    print(f"Sentiment Shift: {'DETECTED' if sentiment_shift.detected else 'None'}")
    print()

    # Step 3: Generate trading signal
    print("Step 3: Trading Signal")
    print("-" * 40)

    # Use verified price or current price
    price_to_use = verification.consensus if verification.verified else current_price

    signal = compass.point_direction(sentiment=0.75, momentum=5.0, current_price=price_to_use)

    print(f"Direction: {signal.direction.value}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Reasoning: {signal.reasoning}")

    if signal.target_price:
        print(f"Target Price: ${signal.target_price:,.2f}")
    if signal.stop_loss:
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")
    print()

    # Step 4: Risk assessment
    print("Step 4: Risk Assessment")
    print("-" * 40)

    risk_level = "LOW"
    if signal.confidence < 0.5:
        risk_level = "HIGH"
    elif signal.confidence < 0.7:
        risk_level = "MEDIUM"

    print(f"Risk Level: {risk_level}")

    if verification.anomalies:
        print("⚠ Anomalies detected - exercise caution")

    if price_spike.detected:
        print("⚠ Price spike detected - volatility risk")
    print()

    # Step 5: Actionable recommendation
    print("Step 5: Recommendation")
    print("-" * 40)

    if signal.direction.value in ["STRONG_BUY", "BUY"]:
        print(f"• {signal.direction.value} signal detected")
        print("• Consider position increase")
        print(f"• Set stop loss at ${signal.stop_loss:,.2f}")
    elif signal.direction.value in ["STRONG_SELL", "SELL"]:
        print(f"• {signal.direction.value} signal detected")
        print("• Consider position reduction")
        print(f"• Set stop loss at ${signal.stop_loss:,.2f}")
    else:
        print("• HOLD signal detected")
        print("• Maintain current position")
        print("• Monitor for changes")

    print()


if __name__ == "__main__":
    generate_trading_signals("BTC", 50000.0)
