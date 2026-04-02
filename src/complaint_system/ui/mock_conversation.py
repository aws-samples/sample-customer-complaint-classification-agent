"""Mock conversation simulator for demo purposes.

This module provides sample conversations and a simulator that plays back
customer-agent dialogues with realistic timing.
"""

import random
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    speaker: str
    message: str


@dataclass
class SampleConversation:
    """A complete sample conversation with metadata."""
    name: str
    description: str
    turns: list[ConversationTurn]
    
    def to_transcript(self) -> str:
        """Convert the conversation to a transcript string."""
        lines = []
        for turn in self.turns:
            lines.append(f"{turn.speaker}: {turn.message}")
        return "\n\n".join(lines)


COMPLAINT_CONVERSATION = SampleConversation(
    name="Billing Dispute",
    description="Customer frustrated about duplicate charges",
    turns=[
        ConversationTurn("Agent", "Thank you for calling AnyBank. My name is Sarah. How can I help you today?"),
        ConversationTurn("Customer", "Hi Sarah. I'm calling because I noticed something wrong with my account. I was charged twice for the same transaction last week."),
        ConversationTurn("Agent", "I'm sorry to hear that. Let me pull up your account. Can you tell me which transaction you're referring to?"),
        ConversationTurn("Customer", "It was a $247.50 charge from Electronics Plus. It shows up twice on the 15th. I've been trying to get this resolved for three weeks now and nobody is helping me!"),
        ConversationTurn("Agent", "I understand your frustration. Let me look into this for you right away."),
        ConversationTurn("Customer", "This is absolutely ridiculous. I've called four times already and each time I'm told someone will call me back, but no one ever does. I want to speak to a manager immediately."),
        ConversationTurn("Agent", "I completely understand, and I apologize for the experience you've had. Let me see what I can do to resolve this for you today."),
        ConversationTurn("Customer", "I've been a customer for 15 years and this is how I'm treated? I'm seriously considering closing my account and going to another bank."),
    ]
)

NORMAL_CONVERSATION = SampleConversation(
    name="Account Inquiry",
    description="Customer asking about account balance and rates",
    turns=[
        ConversationTurn("Agent", "Good afternoon, thank you for calling AnyBank. This is Michael speaking. How may I assist you?"),
        ConversationTurn("Customer", "Hi Michael. I'd like to check my account balance and see if my recent deposit has cleared."),
        ConversationTurn("Agent", "Of course, I'd be happy to help with that. I've pulled up your account. Your current balance is $3,542.18 and yes, your deposit from Monday has cleared."),
        ConversationTurn("Customer", "Great, thank you. I also wanted to ask about your current interest rates on savings accounts."),
        ConversationTurn("Agent", "Our standard savings account currently offers 0.5% APY, and our high-yield savings account offers 4.25% APY with a minimum balance of $1,000."),
        ConversationTurn("Customer", "That high-yield rate sounds good. What would I need to do to open one of those?"),
        ConversationTurn("Agent", "I can help you set that up right now if you'd like. It only takes a few minutes and there are no fees to open the account."),
        ConversationTurn("Customer", "That would be wonderful. Let's do it."),
    ]
)

SAMPLE_CONVERSATIONS = [COMPLAINT_CONVERSATION, NORMAL_CONVERSATION]


class ConversationSimulator:
    """Simulates a conversation playback with callbacks for UI updates."""
    
    def __init__(
        self,
        conversation: SampleConversation,
        on_turn: Callable[[ConversationTurn, int], None],
        min_delay: float = 1.0,
        max_delay: float = 3.0
    ):
        self.conversation = conversation
        self.on_turn = on_turn
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._current_index = 0
        self._is_playing = False
    
    def play_all(self) -> str:
        """Play all turns and return the full transcript."""
        self._is_playing = True
        self._current_index = 0
        
        for i, turn in enumerate(self.conversation.turns):
            if not self._is_playing:
                break
            self.on_turn(turn, i)
            if i < len(self.conversation.turns) - 1:
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)
        
        self._is_playing = False
        return self.conversation.to_transcript()
    
    def stop(self) -> None:
        """Stop the conversation playback."""
        self._is_playing = False
