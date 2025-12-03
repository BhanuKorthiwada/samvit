"""Integration tests for policy RAG functionality."""

import pytest
from httpx import AsyncClient

SAMPLE_POLICY_CONTENT = """# Test Policy

## Section 1: Overview

This is a test policy document for integration testing. It contains information about employee conduct and workplace guidelines.

## Section 2: Working Hours

Standard working hours are from 9:00 AM to 6:00 PM with a one-hour lunch break. Employees must log their attendance through the SAMVIT system.

### 2.1 Flexible Hours

Core hours are from 10:00 AM to 4:00 PM. Employees may adjust their start and end times around the core hours as long as they complete 8 hours per day.

## Section 3: Leave Policy

Employees are entitled to:
- 12 days of casual leave per year
- 12 days of sick leave per year
- 15 days of earned leave per year

Leave requests must be submitted through the SAMVIT HRMS system at least 3 days in advance for planned leave.

## Section 4: Dress Code

Business casual attire is required Monday through Thursday. Fridays are casual dress days. Client-facing employees should dress formally when meeting clients.
"""


class TestPolicyManagement:
    """Test policy CRUD operations."""

    @pytest.mark.asyncio
    async def test_upload_policy(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test uploading a policy document."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Test Policy",
                "category": "general",
                "description": "A test policy for integration tests",
                "version": "1.0",
            },
            files={
                "file": (
                    "test_policy.md",
                    SAMPLE_POLICY_CONTENT.encode(),
                    "text/markdown",
                ),
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Policy"
        assert data["category"] == "general"
        assert data["file_type"] == "md"
        assert data["is_indexed"] is False

    @pytest.mark.asyncio
    async def test_list_policies(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test listing policies."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "List Test Policy",
                "category": "leave",
            },
            files={
                "file": ("policy.md", b"# Test Content", "text/markdown"),
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/policies",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_policy(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test getting a single policy."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        upload_response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Get Test Policy",
                "category": "attendance",
            },
            files={
                "file": ("policy.md", b"# Attendance Policy", "text/markdown"),
            },
            headers=headers,
        )

        policy_id = upload_response.json()["id"]

        response = await client.get(
            f"/api/v1/policies/{policy_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policy_id
        assert data["name"] == "Get Test Policy"

    @pytest.mark.asyncio
    async def test_update_policy(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test updating policy metadata."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        upload_response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Update Test Policy",
                "category": "general",
            },
            files={
                "file": ("policy.md", b"# Test Policy", "text/markdown"),
            },
            headers=headers,
        )

        policy_id = upload_response.json()["id"]

        response = await client.patch(
            f"/api/v1/policies/{policy_id}",
            json={
                "name": "Updated Policy Name",
                "description": "Updated description",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Policy Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_policy(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test deleting a policy."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        upload_response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Delete Test Policy",
                "category": "general",
            },
            files={
                "file": ("policy.md", b"# Test Policy", "text/markdown"),
            },
            headers=headers,
        )

        policy_id = upload_response.json()["id"]

        delete_response = await client.delete(
            f"/api/v1/policies/{policy_id}",
            headers=headers,
        )

        assert delete_response.status_code == 200

        get_response = await client.get(
            f"/api/v1/policies/{policy_id}",
            headers=headers,
        )

        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_duplicate_policy_fails(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test that uploading a policy with duplicate name fails."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Duplicate Test Policy",
                "category": "general",
            },
            files={
                "file": ("policy1.md", b"# First Policy", "text/markdown"),
            },
            headers=headers,
        )

        response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Duplicate Test Policy",
                "category": "general",
            },
            files={
                "file": ("policy2.md", b"# Second Policy", "text/markdown"),
            },
            headers=headers,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()


class TestPolicyIndexing:
    """Test policy indexing for RAG."""

    @pytest.mark.asyncio
    async def test_index_single_policy(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test indexing a single policy."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        upload_response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Index Test Policy",
                "category": "general",
            },
            files={
                "file": ("policy.md", SAMPLE_POLICY_CONTENT.encode(), "text/markdown"),
            },
            headers=headers,
        )

        policy_id = upload_response.json()["id"]

        index_response = await client.post(
            f"/api/v1/policies/{policy_id}/index",
            headers=headers,
        )

        assert index_response.status_code == 200
        data = index_response.json()
        assert data["indexed_count"] == 1
        assert data["total_chunks"] > 0

        get_response = await client.get(
            f"/api/v1/policies/{policy_id}",
            headers=headers,
        )

        assert get_response.json()["is_indexed"] is True

    @pytest.mark.asyncio
    async def test_index_all_policies(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test batch indexing of policies."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        for i in range(3):
            await client.post(
                "/api/v1/policies/upload",
                data={
                    "name": f"Batch Index Policy {i}",
                    "category": "general",
                },
                files={
                    "file": (
                        "policy.md",
                        f"# Policy {i}\n\nContent for policy {i}".encode(),
                        "text/markdown",
                    ),
                },
                headers=headers,
            )

        index_response = await client.post(
            "/api/v1/policies/index",
            json={"force": False},
            headers=headers,
        )

        assert index_response.status_code == 200
        data = index_response.json()
        assert data["indexed_count"] >= 3

    @pytest.mark.asyncio
    async def test_vectorstore_stats(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test getting vector store statistics."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        response = await client.get(
            "/api/v1/policies/stats",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "total_chunks" in data


class TestPolicyRAGChat:
    """Test RAG-based policy chat."""

    @pytest.mark.asyncio
    async def test_policy_chat_with_indexed_content(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test chatting about indexed policy content."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        upload_response = await client.post(
            "/api/v1/policies/upload",
            data={
                "name": "Chat Test Policy",
                "category": "leave",
            },
            files={
                "file": (
                    "leave_policy.md",
                    SAMPLE_POLICY_CONTENT.encode(),
                    "text/markdown",
                ),
            },
            headers=headers,
        )

        policy_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/policies/{policy_id}/index",
            headers=headers,
        )

        chat_response = await client.post(
            "/api/v1/ai/policy-chat",
            json={
                "question": "What are the working hours?",
            },
            headers=headers,
        )

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert "answer" in data
        assert "sources" in data

    @pytest.mark.asyncio
    async def test_policy_chat_no_results(
        self,
        client: AsyncClient,
        test_tenant,
        test_user,
    ):
        """Test chat when no relevant policies found."""
        from tests.conftest import get_auth_headers

        headers = get_auth_headers(test_user, test_tenant)

        response = await client.post(
            "/api/v1/ai/policy-chat",
            json={
                "question": "What is the company's policy on intergalactic travel?",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestDocumentLoader:
    """Test document loading and chunking."""

    def test_load_markdown_file(self, tmp_path):
        """Test loading a markdown file."""
        from app.ai.rag.document_loader import DocumentLoader

        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is test content.")

        loader = DocumentLoader()
        content = loader.load_file(test_file)

        assert "# Test" in content
        assert "This is test content" in content

    def test_load_text_file(self, tmp_path):
        """Test loading a text file."""
        from app.ai.rag.document_loader import DocumentLoader

        test_file = tmp_path / "test.txt"
        test_file.write_text("Plain text content here.")

        loader = DocumentLoader()
        content = loader.load_file(test_file)

        assert content == "Plain text content here."

    def test_chunk_text(self):
        """Test text chunking."""
        from app.ai.rag.document_loader import ChunkingConfig, DocumentLoader

        config = ChunkingConfig(chunk_size=100, chunk_overlap=20)
        loader = DocumentLoader(config)

        long_text = "This is a sentence. " * 50

        chunks = loader.chunk_text(long_text, source_file="test.txt")

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 150
            assert chunk.source_file == "test.txt"

    def test_load_and_chunk(self, tmp_path):
        """Test combined load and chunk."""
        from app.ai.rag.document_loader import DocumentLoader

        test_file = tmp_path / "policy.md"
        test_file.write_text(SAMPLE_POLICY_CONTENT)

        loader = DocumentLoader()
        chunks = loader.load_and_chunk(test_file, metadata={"test": True})

        assert len(chunks) > 0
        assert all(c.metadata.get("test") is True for c in chunks)

    def test_unsupported_file_type(self, tmp_path):
        """Test error on unsupported file type."""
        from app.ai.rag.document_loader import DocumentLoader

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx content")

        loader = DocumentLoader()

        with pytest.raises(ValueError, match="Unsupported file type"):
            loader.load_file(test_file)


class TestVectorStore:
    """Test vector store operations."""

    # Fixed IDs for vector store unit tests
    VECTORSTORE_TEST_TENANT = "00000000-0000-0000-0000-000000000099"
    VECTORSTORE_TEST_POLICY = "00000000-0000-0000-0000-000000000098"

    def test_add_and_query_chunks(self):
        """Test adding chunks and querying."""
        from app.ai.rag.document_loader import DocumentChunk
        from app.ai.rag.vectorstore import PolicyVectorStore

        store = PolicyVectorStore(self.VECTORSTORE_TEST_TENANT)
        store.clear()  # Clean before test

        chunks = [
            DocumentChunk(
                content="Employees are entitled to 12 days of casual leave per year.",
                metadata={"policy_name": "Leave Policy"},
                chunk_index=0,
                source_file="leave.md",
            ),
            DocumentChunk(
                content="Sick leave is 12 days per year with medical certificate required.",
                metadata={"policy_name": "Leave Policy"},
                chunk_index=1,
                source_file="leave.md",
            ),
        ]

        added = store.add_chunks(chunks, self.VECTORSTORE_TEST_POLICY)
        assert added == 2

        results = store.query("How many casual leave days?", n_results=2)
        assert len(results) > 0
        assert "casual leave" in results[0]["content"].lower()

        store.clear()

    def test_delete_policy_from_store(self):
        """Test deleting policy chunks."""
        from app.ai.rag.document_loader import DocumentChunk
        from app.ai.rag.vectorstore import PolicyVectorStore

        store = PolicyVectorStore(self.VECTORSTORE_TEST_TENANT)
        store.clear()  # Clean before test

        chunks = [
            DocumentChunk(
                content="Test content for deletion",
                metadata={},
                chunk_index=0,
                source_file="test.md",
            ),
        ]

        store.add_chunks(chunks, self.VECTORSTORE_TEST_POLICY)

        deleted = store.delete_policy(self.VECTORSTORE_TEST_POLICY)
        assert deleted == 1

        results = store.query("Test content", n_results=1)
        matching = [
            r for r in results if self.VECTORSTORE_TEST_POLICY in r.get("id", "")
        ]
        assert len(matching) == 0

        store.clear()

    def test_get_stats(self):
        """Test getting store statistics."""
        from app.ai.rag.vectorstore import PolicyVectorStore

        store = PolicyVectorStore(self.VECTORSTORE_TEST_TENANT)
        store.clear()  # Clean before test

        stats = store.get_stats()
        assert stats["tenant_id"] == self.VECTORSTORE_TEST_TENANT
        assert "total_chunks" in stats
        assert "policies" in stats

        store.clear()
