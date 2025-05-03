"""Example of extending AIEngine with custom functionality."""

from typing import List, Optional, Type

from pydantic import BaseModel

from utils.ai_engine import AIEngine, AIEngineError


class SpecializedAIEngine(AIEngine):
    """A specialized version of AIEngine with domain-specific functionality.

    This class demonstrates how to extend AIEngine with custom behavior
    through inheritance.
    """

    def _setup_instrumentation(self):
        """Override to customize instrumentation.

        This method demonstrates overriding protected extension points.
        """
        # Use parent's instrumentation or add custom monitoring
        base_instrument = super()._setup_instrumentation()

        # Here you could add additional custom monitoring
        # For example, integrate with a different monitoring service

        return base_instrument

    def _get_provider_settings(self):
        """Override to customize provider settings.

        This method demonstrates how to customize default provider settings.
        """
        settings = super()._get_provider_settings()

        # Customize settings based on the provider
        if self.provider == "openai":
            settings.frequency_penalty = 0.5

        elif self.provider == "anthropic":
            settings.temperature = 0.4

        return settings

    async def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text.

        This method demonstrates adding new domain-specific functionality
        on top of the base AIEngine capabilities.

        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keywords
        """
        system_prompt = (
            f"You are a keyword extraction tool. Extract up to {max_keywords} "
            f"important keywords from the provided text. Return only the keywords "
            f"as a comma-separated list, with no additional text."
        )

        try:
            result = await self.generate(
                prompt=text,
                system=system_prompt,
                temperature=0.2
            )

            # Process the result into a list
            keywords = [kw.strip() for kw in result.split(',')]

            # Limit to max_keywords
            return keywords[:max_keywords]

        except Exception as e:
            raise AIEngineError(f"Keyword extraction failed: {str(e)}")

    async def analyze_sentiment_with_confidence(
        self,
        text: str
    ) -> dict:
        """Analyze sentiment with confidence scores.

        This method demonstrates building a more specialized analysis tool
        on top of the base AIEngine.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment analysis and confidence score
        """
        # Create a specialized system prompt
        system_prompt = (
            "You are a sentiment analysis tool. Analyze the sentiment of the "
            "provided text and return JSON with 'sentiment' (positive, negative, or neutral) "
            "and 'confidence' (a float between 0 and 1)."
        )

        # Use structured output by defining a schema
        class SentimentAnalysis(BaseModel):
            """Schema for sentiment analysis output."""
            sentiment: str
            confidence: float

        try:
            # Generate with structured output
            result = await self.generate(
                prompt=text,
                system=system_prompt,
                output_schema=SentimentAnalysis,
                temperature=0.1
            )

            # Return the structured output
            return {
                "sentiment": result.sentiment,
                "confidence": result.confidence,
                "text": text[:100] + "..." if len(text) > 100 else text
            }

        except Exception as e:
            raise AIEngineError(f"Sentiment analysis failed: {str(e)}")


# Example usage
async def main():
    # Create the specialized engine
    engine = SpecializedAIEngine(
        feature_name="content_analyzer",
        model_name="openai:gpt-4-turbo"
    )

    # Use the specialized methods
    text = "The new product release exceeded all expectations and customers are extremely happy with the features."

    keywords = await engine.extract_keywords(text)
    print(f"Keywords: {keywords}")

    sentiment = await engine.analyze_sentiment_with_confidence(text)
    print(f"Sentiment: {sentiment['sentiment']}")
    print(f"Confidence: {sentiment['confidence']:.2f}")

    # Use the inherited methods
    classification = await engine.classify(
        content=text,
        categories=["product announcement",
                    "customer feedback", "technical update"]
    )
    print(f"Classification: {classification}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
