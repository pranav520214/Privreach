using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PrivreachDesktop.Models;

public class SystemStatusDto
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "offline";

    [JsonPropertyName("engine_running")]
    public bool EngineRunning { get; set; }

    [JsonPropertyName("gemma_embedded")]
    public bool GemmaEmbedded { get; set; }

    [JsonPropertyName("ollama_port")]
    public int OllamaPort { get; set; } = 11434;

    [JsonPropertyName("router_model")]
    public string RouterModel { get; set; } = "";

    [JsonPropertyName("synthesis_model")]
    public string SynthesisModel { get; set; } = "";

    [JsonPropertyName("verifier_model")]
    public string VerifierModel { get; set; } = "";

    [JsonPropertyName("indexed_chunks")]
    public int IndexedChunks { get; set; }

    [JsonPropertyName("indexed_documents")]
    public int IndexedDocuments { get; set; }

    [JsonPropertyName("total_chunks")]
    public int TotalChunks { get; set; }

    [JsonPropertyName("ram_usage_mb")]
    public double RamUsageMb { get; set; }

    [JsonPropertyName("vram_usage_mb")]
    public double VramUsageMb { get; set; }

    [JsonPropertyName("cpu_percent")]
    public double CpuPercent { get; set; }

    [JsonPropertyName("airgap_active")]
    public bool AirgapActive { get; set; } = true;
}

public class QueryAnalysisDto
{
    [JsonPropertyName("risk_level")]
    public string RiskLevel { get; set; } = "MEDIUM";

    [JsonPropertyName("task_type")]
    public string TaskType { get; set; } = "LITERATURE_REVIEW";

    [JsonPropertyName("scientific_domain")]
    public string ScientificDomain { get; set; } = "";

    [JsonPropertyName("key_entities")]
    public List<string> KeyEntities { get; set; } = new();

    [JsonPropertyName("lexical_keywords")]
    public List<string> LexicalKeywords { get; set; } = new();

    [JsonPropertyName("semantic_queries")]
    public List<string> SemanticQueries { get; set; } = new();

    [JsonPropertyName("adversarial_audit_required")]
    public bool AdversarialAuditRequired { get; set; } = true;

    [JsonPropertyName("analysis_rationale")]
    public string AnalysisRationale { get; set; } = "";
}

public class ClaimDto
{
    [JsonPropertyName("claim_id")]
    public int ClaimId { get; set; }

    [JsonPropertyName("text")]
    public string Text { get; set; } = "";

    [JsonPropertyName("status")]
    public string Status { get; set; } = "UNSUPPORTED";

    [JsonPropertyName("source_doc")]
    public string SourceDoc { get; set; } = "";

    [JsonPropertyName("source_page")]
    public int? SourcePage { get; set; }

    [JsonPropertyName("evidence_quote")]
    public string EvidenceQuote { get; set; } = "";

    [JsonPropertyName("critique")]
    public string Critique { get; set; } = "";

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    // Helper UI formatting properties
    [JsonIgnore]
    public string StatusBadge => Status switch
    {
        "VERIFIED" => "✓ VERIFIED",
        "UNSUPPORTED" => "⚠️ UNSUPPORTED",
        "CONTRADICTED" => "❌ CONTRADICTION",
        "PARTIAL" => "⚡ PARTIAL",
        _ => Status
    };

    [JsonIgnore]
    public string CitationReference => !string.IsNullOrEmpty(SourceDoc) 
        ? $"{SourceDoc} (p. {(SourcePage.HasValue ? SourcePage.Value.ToString() : "?")})" 
        : "Uncited";
}

public class VerificationSummaryDto
{
    [JsonPropertyName("grounding_confidence_pct")]
    public double GroundingConfidencePct { get; set; }

    [JsonPropertyName("total_claims")]
    public int TotalClaims { get; set; }

    [JsonPropertyName("verified_claims")]
    public int VerifiedClaims { get; set; }

    [JsonPropertyName("unsupported_claims")]
    public int UnsupportedClaims { get; set; }

    [JsonPropertyName("contradicted_claims")]
    public int ContradictedClaims { get; set; }

    [JsonPropertyName("claims")]
    public List<ClaimDto> Claims { get; set; } = new();
}

public class CalculationAuditDto
{
    [JsonPropertyName("equation_latex")]
    public string EquationLatex { get; set; } = "";

    [JsonPropertyName("target_variable")]
    public string TargetVariable { get; set; } = "";

    [JsonPropertyName("variables")]
    public Dictionary<string, object> Variables { get; set; } = new();

    [JsonPropertyName("units")]
    public Dictionary<string, string> Units { get; set; } = new();

    [JsonPropertyName("model_predicted_value")]
    public string? ModelPredictedValue { get; set; }

    [JsonPropertyName("deterministic_computed_value")]
    public string? DeterministicComputedValue { get; set; }

    [JsonPropertyName("is_verified")]
    public bool IsVerified { get; set; }

    [JsonPropertyName("relative_error_pct")]
    public double? RelativeErrorPct { get; set; }

    [JsonPropertyName("verification_status")]
    public string VerificationStatus { get; set; } = "";

    [JsonPropertyName("verification_details")]
    public string VerificationDetails { get; set; } = "";

    [JsonPropertyName("code_executed")]
    public string CodeExecuted { get; set; } = "";
}

public class RetrievedChunkDto
{
    [JsonPropertyName("chunk_id")]
    public string ChunkId { get; set; } = "";

    [JsonPropertyName("doc_name")]
    public string DocName { get; set; } = "";

    [JsonPropertyName("page_num")]
    public int PageNum { get; set; } = 1;

    [JsonPropertyName("section_header")]
    public string SectionHeader { get; set; } = "";

    [JsonPropertyName("text")]
    public string Text { get; set; } = "";

    [JsonPropertyName("rrf_score")]
    public double RrfScore { get; set; }

    [JsonPropertyName("final_rank")]
    public int FinalRank { get; set; }

    [JsonPropertyName("evidence_type")]
    public string EvidenceType { get; set; } = "DOCUMENT_PAGE";

    [JsonPropertyName("media_path")]
    public string? MediaPath { get; set; }

    [JsonIgnore]
    public bool HasImage => !string.IsNullOrEmpty(MediaPath) && System.IO.File.Exists(MediaPath);

    [JsonIgnore]
    public string EvidenceTypeBadge => EvidenceType switch
    {
        "MATHEMATICAL_FORMULA" => "📐 FORMULA",
        "STRUCTURED_TABLE" => "📊 TABLE",
        "VISUAL_FIGURE" => "🔬 FIGURE",
        "VIDEO_TIMECODE" => "🎬 VIDEO",
        "AUDIO_TRANSCRIPT" => "🎙️ AUDIO",
        _ => "📄 TEXT"
    };
}

public class ReasoningStepDto
{
    [JsonPropertyName("step_number")]
    public int StepNumber { get; set; } = 1;

    [JsonPropertyName("stage")]
    public string Stage { get; set; } = "PROBLEM_FORMULATION";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("content")]
    public string Content { get; set; } = "";

    [JsonPropertyName("status")]
    public string Status { get; set; } = "COMPLETED";
}

public class QueryResultDto
{
    [JsonPropertyName("query")]
    public string Query { get; set; } = "";

    [JsonPropertyName("query_analysis")]
    public QueryAnalysisDto? QueryAnalysis { get; set; }

    [JsonPropertyName("synthesis_text")]
    public string SynthesisText { get; set; } = "";

    [JsonPropertyName("verification")]
    public VerificationSummaryDto? Verification { get; set; }

    [JsonPropertyName("calculation_audit")]
    public CalculationAuditDto? CalculationAudit { get; set; }

    [JsonPropertyName("derivation_markdown")]
    public string DerivationMarkdown { get; set; } = "";

    [JsonPropertyName("multimodal_timeline_markdown")]
    public string MultimodalTimelineMarkdown { get; set; } = "";

    [JsonPropertyName("visual_evidence_markdown")]
    public string VisualEvidenceMarkdown { get; set; } = "";

    [JsonPropertyName("deep_thinking_markdown")]
    public string DeepThinkingMarkdown { get; set; } = "";

    [JsonPropertyName("reasoning_trace")]
    public string? ReasoningTrace { get; set; }

    [JsonPropertyName("reasoning_steps")]
    public List<ReasoningStepDto> ReasoningSteps { get; set; } = new();

    [JsonPropertyName("thinking_duration_s")]
    public double? ThinkingDurationS { get; set; }

    [JsonPropertyName("graph_markdown")]
    public string GraphMarkdown { get; set; } = "";

    [JsonPropertyName("cross_document_bridges")]
    public List<CrossDocBridgeDto> CrossDocBridges { get; set; } = new();

    [JsonPropertyName("graph_subnetwork")]
    public GraphSubnetworkDto? GraphSubnetwork { get; set; }

    [JsonPropertyName("retrieved_chunks")]
    public List<RetrievedChunkDto> RetrievedChunks { get; set; } = new();

    [JsonPropertyName("execution_stats")]
    public Dictionary<string, object> ExecutionStats { get; set; } = new();
}

public class CrossDocBridgeDto
{
    [JsonPropertyName("entity")]
    public string Entity { get; set; } = "";

    [JsonPropertyName("documents")]
    public List<string> Documents { get; set; } = new();

    [JsonPropertyName("chunk_ids")]
    public List<string> ChunkIds { get; set; } = new();

    [JsonPropertyName("shared_relations")]
    public List<string> SharedRelations { get; set; } = new();

    [JsonIgnore]
    public string DocumentsSummary => string.Join(" ⟷ ", Documents);

    [JsonIgnore]
    public string RelationsSummary => SharedRelations.Count > 0 ? string.Join(", ", SharedRelations) : "MENTIONS";
}

public class GraphNodeDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("label")]
    public string Label { get; set; } = "";

    [JsonPropertyName("type")]
    public string Type { get; set; } = "ENTITY";

    [JsonPropertyName("doc_name")]
    public string? DocName { get; set; }

    [JsonPropertyName("page_num")]
    public int? PageNum { get; set; }

    [JsonPropertyName("degree")]
    public int Degree { get; set; }

    [JsonPropertyName("community_id")]
    public int CommunityId { get; set; }
}

public class GraphEdgeDto
{
    [JsonPropertyName("source")]
    public string Source { get; set; } = "";

    [JsonPropertyName("target")]
    public string Target { get; set; } = "";

    [JsonPropertyName("relation")]
    public string Relation { get; set; } = "RELATES_TO";

    [JsonPropertyName("weight")]
    public double Weight { get; set; } = 1.0;

    [JsonPropertyName("is_cross_document")]
    public bool IsCrossDocument { get; set; }
}

public class GraphCommunityDto
{
    [JsonPropertyName("community_id")]
    public int CommunityId { get; set; }

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("summary")]
    public string Summary { get; set; } = "";

    [JsonPropertyName("members")]
    public List<string> Members { get; set; } = new();
}

public class GraphSubnetworkDto
{
    [JsonPropertyName("nodes")]
    public List<GraphNodeDto> Nodes { get; set; } = new();

    [JsonPropertyName("edges")]
    public List<GraphEdgeDto> Edges { get; set; } = new();

    [JsonPropertyName("bridges")]
    public List<CrossDocBridgeDto> Bridges { get; set; } = new();

    [JsonPropertyName("communities")]
    public List<GraphCommunityDto> Communities { get; set; } = new();

    [JsonPropertyName("total_nodes")]
    public int TotalNodes { get; set; }

    [JsonPropertyName("total_edges")]
    public int TotalEdges { get; set; }
}

public class DocumentDto
{
    [JsonPropertyName("doc_name")]
    public string DocName { get; set; } = "";

    [JsonPropertyName("path")]
    public string Path { get; set; } = "";

    [JsonPropertyName("type")]
    public string Type { get; set; } = "pdf";

    [JsonPropertyName("chunks")]
    public int Chunks { get; set; }
}

public class DocumentsResultDto
{
    [JsonPropertyName("documents")]
    public List<DocumentDto> Documents { get; set; } = new();

    [JsonPropertyName("total_count")]
    public int TotalCount { get; set; }

    [JsonPropertyName("total_chunks")]
    public int TotalChunks { get; set; }
}

public class ModelsResultDto
{
    [JsonPropertyName("models")]
    public List<string> Models { get; set; } = new();

    [JsonPropertyName("active_router")]
    public string ActiveRouter { get; set; } = "";

    [JsonPropertyName("active_synthesis")]
    public string ActiveSynthesis { get; set; } = "";

    [JsonPropertyName("active_verifier")]
    public string ActiveVerifier { get; set; } = "";
}

public class IngestResultDto
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "";

    [JsonPropertyName("doc_name")]
    public string DocName { get; set; } = "";

    [JsonPropertyName("chunks")]
    public int Chunks { get; set; }

    [JsonPropertyName("total_ram_chunks")]
    public int TotalRamChunks { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

public class UpdaterStatusDto
{
    [JsonPropertyName("version")]
    public string Version { get; set; } = "2.0.0";

    [JsonPropertyName("channel")]
    public string Channel { get; set; } = "stable";

    [JsonPropertyName("release_date")]
    public string ReleaseDate { get; set; } = "";

    [JsonPropertyName("git_commit")]
    public string GitCommit { get; set; } = "";

    [JsonPropertyName("total_snapshots")]
    public int TotalSnapshots { get; set; }

    [JsonPropertyName("latest_snapshot")]
    public string? LatestSnapshot { get; set; }

    [JsonPropertyName("can_rollback")]
    public bool CanRollback { get; set; }
}

public class UpdateCheckResultDto
{
    [JsonPropertyName("has_update")]
    public bool HasUpdate { get; set; }

    [JsonPropertyName("current_version")]
    public string CurrentVersion { get; set; } = "";

    [JsonPropertyName("latest_version")]
    public string LatestVersion { get; set; } = "";

    [JsonPropertyName("channel")]
    public string Channel { get; set; } = "stable";

    [JsonPropertyName("release_date")]
    public string? ReleaseDate { get; set; }

    [JsonPropertyName("changelog")]
    public string? Changelog { get; set; }

    [JsonPropertyName("download_url")]
    public string? DownloadUrl { get; set; }

    [JsonPropertyName("is_patch")]
    public bool IsPatch { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}

public class PatchResultDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("patch_id")]
    public string PatchId { get; set; } = "";

    [JsonPropertyName("target_version")]
    public string TargetVersion { get; set; } = "";

    [JsonPropertyName("operations_applied")]
    public int OperationsApplied { get; set; }

    [JsonPropertyName("files_modified")]
    public List<string> FilesModified { get; set; } = new();

    [JsonPropertyName("hot_reloaded_modules")]
    public List<string> HotReloadedModules { get; set; } = new();

    [JsonPropertyName("snapshot_id")]
    public string? SnapshotId { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

public class RollbackResultDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("snapshot_id")]
    public string SnapshotId { get; set; } = "";

    [JsonPropertyName("restored_files")]
    public List<string> RestoredFiles { get; set; } = new();

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}
