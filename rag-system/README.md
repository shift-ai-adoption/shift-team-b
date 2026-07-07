# RAG System (Issue #7)

WEBUIを備えたフラットベクトルRAGシステム。

## 構成

| サービス | 外部ポート | 説明 |
|---------|-----------|------|
| frontend | **8081** | React WEBUI（nginx、Basic認証、`/api/*` をbackendへプロキシ） |
| backend | **8001** | FastAPI REST API（Basic認証。UIを介さないAPIテスト用に直接公開） |
| pgvector | 内部のみ | PostgreSQL 16 + pgvector |
| chromadb | 内部のみ | ChromaDB |
| qdrant | 内部のみ | Qdrant |

- 認証: Basic認証 `admin / admin123!`
- Embedding: Amazon Bedrock `amazon.titan-embed-text-v2:0` (1024次元)
- LLM: Amazon Bedrock `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- 文書は **3つのベクトルDBに同時登録** され、検索・評価でDBを切替/比較できる

## 起動

```bash
cd rag-system
docker-compose up -d --build
```

AWSクレデンシャルはホストの環境変数（`AWS_ACCESS_KEY_ID` 等）から渡されます。

## 画面と API のマッピング

| 画面 | 主なAPI |
|------|---------|
| 検索 | `POST /api/search`, `GET /api/search/compare` |
| アップロード | `POST /api/upload`, `POST /api/vectorize` |
| 文書管理 | `GET /api/documents`, `POST /api/documents/{id}/rollback`, `DELETE /api/documents/{id}` |
| 検索履歴 | `GET /api/history`, `GET /api/history/{id}`, `POST /api/history/{id}/rating` |
| テンプレート | `GET/POST /api/templates`, `PUT/DELETE /api/templates/{id}`, `GET /api/export/{history_id}` |
| DB評価 | `POST /api/evaluation`, `GET /api/evaluation/summary` |
| 設定 | `GET/PUT /api/settings` |

## UIを使わないAPIテスト例

```bash
BASE=http://localhost:8001
AUTH="admin:admin123!"

# 1. アップロード（ファイル保存のみ）
curl -u $AUTH -F "file=@sample.md" -F "visibility_level=1" $BASE/api/upload

# 2. ベクトル化（3DB同時登録）
curl -u $AUTH -H "Content-Type: application/json" \
  -d '{"version_id": 1, "chunk_size": 512}' $BASE/api/vectorize

# 3. 検索（LLM回答つき）
curl -u $AUTH -H "Content-Type: application/json" \
  -d '{"query": "○○について教えて", "db": "pgvector", "role": "general"}' \
  $BASE/api/search

# 4. 3DB比較検索
curl -u $AUTH "$BASE/api/search/compare?query=テスト&role=general"

# 5. 定量評価
curl -u $AUTH -H "Content-Type: application/json" \
  -d '{"query": "○○とは", "expected_filename": "sample.md"}' $BASE/api/evaluation

# 6. 結果のエクスポート (markdown | word | excel)
curl -u $AUTH -o result.xlsx "$BASE/api/export/1?format=excel"
```

## 要件との対応

| 要件 | 実装 |
|------|------|
| 1. docker-compose構成 | `docker-compose.yml`（5サービス） |
| 2. 外部アクセス/内部通信 | 8081/8001のみ外部公開、DB3種は内部ネットワークのみ |
| 3. 接続元制限なし | `0.0.0.0` バインド、CORS全許可 |
| 4. 空きポート利用 | SG許可済み&未使用の8081/8001を使用 |
| 5. Basic認証 | nginx + FastAPIミドルウェア両方で検証 |
| 6. 画面ごとのHTTP API | 全画面がREST APIのみで操作可能（上表参照） |
| 7. アップロード/ベクトル化の分離 | `/api/upload` と `/api/vectorize` を分離 |
| 8. バージョン管理 | 同名ファイルで自動バージョンアップ、ロールバック可 |
| 9. プロンプト履歴 | `search_history` にプロンプト全文・結果を保存 |
| 10-11. 出力フォーマット/テンプレート | markdown/word/excel、初期テンプレート3種 |
| 12. 役職による閲覧制御 | 文書の`visibility_level` × 検索時の`role` |
| 13. 定性・定量評価 | ★評価(定性) + Hit Rate/MRR/レイテンシ(定量) |
| 14. チャンクサイズ選択・編集 | 候補選択 + 直接編集（設定画面/ベクトル化時） |
| 15. 複数ベクトルDB同時登録・評価 | pgvector/Chroma/Qdrantへ同時登録、比較・評価API |
