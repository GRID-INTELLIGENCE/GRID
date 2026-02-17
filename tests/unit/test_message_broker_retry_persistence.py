import pytest

# MessageBroker pending migration from legacy_src/
MessageBroker = None


@pytest.mark.skipif(MessageBroker is None, reason="MessageBroker pending migration")
class TestMessageBroker:
    @pytest.fixture
    def broker(self):
        return MessageBroker()

    def test_broker_persists_retry_record_and_moves_to_dlq(self, broker):
        msg_id = "msg123"
        msg_content = {"data": "test"}

        # Initial failure (attempt 1)
        should_retry = broker.handle_message_failure(msg_id, msg_content, "Error 1")
        assert should_retry
        assert broker.retry_records[msg_id].attempts == 1

        # Second failure (attempt 2)
        should_retry = broker.handle_message_failure(msg_id, msg_content, "Error 2")
        assert should_retry
        assert broker.retry_records[msg_id].attempts == 2

        # Third failure (attempt 3)
        should_retry = broker.handle_message_failure(msg_id, msg_content, "Error 3")
        assert should_retry
        assert broker.retry_records[msg_id].attempts == 3

        # Fourth failure - Max retries exceeded (default max_retries=3)
        should_retry = broker.handle_message_failure(msg_id, msg_content, "Error 4")
        assert not should_retry
        assert len(broker.dlq.get_all()) == 1
        assert broker.dlq.get_all()[0]["message"] == msg_content
        assert "Max retries exceeded" in broker.dlq.get_all()[0]["error"]
