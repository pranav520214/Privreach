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

    [JsonPropertyName("hardware_locked")]
    public bool HardwareLocked { get; set; } = true;

    [JsonPropertyName("cpu_id")]
    public string CpuId { get; set; } = "";

    [JsonPropertyName("cpu_model")]
    public string CpuModel { get; set; } = "";

    [JsonPropertyName("hardware_verified")]
    public bool HardwareVerified { get; set; } = true;
}

public class HardwareAuthStatusDto
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "enforced";

    [JsonPropertyName("verified")]
    public bool Verified { get; set; } = true;

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";

    [JsonPropertyName("encryption_algorithm")]
    public string EncryptionAlgorithm { get; set; } = "AES-256-GCM + Argon2id";

    [JsonPropertyName("storage_theft_protection")]
    public string StorageTheftProtection { get; set; } = "PHYSICAL_CPU_BOUND";
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

public class SolveResultDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("result")]
    public double? Result { get; set; }

    [JsonPropertyName("formula_str")]
    public string FormulaStr { get; set; } = "";

    [JsonPropertyName("code_executed")]
    public string CodeExecuted { get; set; } = "";

    [JsonPropertyName("equation")]
    public string Equation { get; set; } = "";

    [JsonPropertyName("target_variable")]
    public string TargetVariable { get; set; } = "";

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

public class ArtifactDto
{
    [JsonPropertyName("artifact_id")]
    public string ArtifactId { get; set; } = "";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("artifact_type")]
    public string ArtifactType { get; set; } = "";

    [JsonPropertyName("created_at")]
    public double CreatedAt { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("source_doc")]
    public string? SourceDoc { get; set; }

    [JsonPropertyName("file_path")]
    public string? FilePath { get; set; }
}

public class ArtifactsResultDto
{
    [JsonPropertyName("artifacts")]
    public List<ArtifactDto> Artifacts { get; set; } = new();

    [JsonPropertyName("total_count")]
    public int TotalCount { get; set; }
}

// ========================================================
// SUBSYSTEM 1 & 2: INGRESS & AIRLOCK CDR DTOs
// ========================================================

public class ManifestEntryDto
{
    [JsonPropertyName("paper_id")]
    public string PaperId { get; set; } = "";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("doi")]
    public string? Doi { get; set; }

    [JsonPropertyName("queue")]
    public string Queue { get; set; } = "archive"; // "priority" or "archive"

    [JsonPropertyName("triage_score")]
    public double TriageScore { get; set; }

    [JsonPropertyName("source")]
    public string Source { get; set; } = "";

    [JsonPropertyName("pdf_filename")]
    public string? PdfFilename { get; set; }

    [JsonPropertyName("pdf_sha256")]
    public string? PdfSha256 { get; set; }

    [JsonPropertyName("pdf_size_bytes")]
    public int PdfSizeBytes { get; set; }

    [JsonPropertyName("download_status")]
    public string DownloadStatus { get; set; } = "pending";

    [JsonIgnore]
    public bool IsPriority => string.Equals(Queue, "priority", StringComparison.OrdinalIgnoreCase);

    [JsonIgnore]
    public string QueueBadge => IsPriority ? "⭐ PRIORITY" : "📦 ARCHIVE";
}

public class HarvestManifestDto
{
    [JsonPropertyName("harvest_id")]
    public string HarvestId { get; set; } = "";

    [JsonPropertyName("query")]
    public string Query { get; set; } = "";

    [JsonPropertyName("expanded_terms")]
    public List<string> ExpandedTerms { get; set; } = new();

    [JsonPropertyName("created_at_utc")]
    public string CreatedAtUtc { get; set; } = "";

    [JsonPropertyName("total_papers")]
    public int TotalPapers { get; set; }

    [JsonPropertyName("priority_count")]
    public int PriorityCount { get; set; }

    [JsonPropertyName("archive_count")]
    public int ArchiveCount { get; set; }

    [JsonPropertyName("entries")]
    public List<ManifestEntryDto> Entries { get; set; } = new();

    [JsonPropertyName("signature")]
    public string? Signature { get; set; }
}

public class HarvestResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("manifest")]
    public HarvestManifestDto? Manifest { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

public class PolyglotCheckDto
{
    [JsonPropertyName("is_polyglot")]
    public bool IsPolyglot { get; set; }

    [JsonPropertyName("detected_formats")]
    public List<string> DetectedFormats { get; set; } = new();

    [JsonPropertyName("details")]
    public string Details { get; set; } = "";
}

public class SanitizationReportDto
{
    [JsonPropertyName("javascript_actions_removed")]
    public int JavascriptActionsRemoved { get; set; }

    [JsonPropertyName("launch_actions_removed")]
    public int LaunchActionsRemoved { get; set; }

    [JsonPropertyName("embedded_files_removed")]
    public int EmbeddedFilesRemoved { get; set; }

    [JsonPropertyName("uri_links_defanged")]
    public int UriLinksDefanged { get; set; }

    [JsonPropertyName("has_modifications")]
    public bool HasModifications { get; set; }
}

public class InjectionCheckDto
{
    [JsonPropertyName("is_flagged")]
    public bool IsFlagged { get; set; }

    [JsonPropertyName("heuristic_matches")]
    public List<string> HeuristicMatches { get; set; } = new();

    [JsonPropertyName("zero_width_chars_found")]
    public int ZeroWidthCharsFound { get; set; }
}

public class CDRResultDto
{
    [JsonPropertyName("is_cleared")]
    public bool IsCleared { get; set; }

    [JsonPropertyName("source_sha256")]
    public string SourceSha256 { get; set; } = "";

    [JsonPropertyName("sanitized_sha256")]
    public string? SanitizedSha256 { get; set; }

    [JsonPropertyName("quarantine_src_path")]
    public string QuarantineSrcPath { get; set; } = "";

    [JsonPropertyName("vault_dest_path")]
    public string? VaultDestPath { get; set; }

    [JsonPropertyName("processed_at_utc")]
    public string ProcessedAtUtc { get; set; } = "";

    [JsonPropertyName("polyglot_check")]
    public PolyglotCheckDto? PolyglotCheck { get; set; }

    [JsonPropertyName("sanitization_report")]
    public SanitizationReportDto? SanitizationReport { get; set; }

    [JsonPropertyName("injection_check")]
    public InjectionCheckDto? InjectionCheck { get; set; }

    [JsonPropertyName("visual_flattening_applied")]
    public bool VisualFlatteningApplied { get; set; }

    [JsonPropertyName("audit_log")]
    public List<string> AuditLog { get; set; } = new();
}

public class AirlockResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("cdr_result")]
    public CDRResultDto? CdrResult { get; set; }

    [JsonPropertyName("ingest_result")]
    public object? IngestResult { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

// ========================================================
// SUBSYSTEM 3: ZERO-HALLUCINATION PROVER DTOs
// ========================================================

public class SpanMatchResultDto
{
    [JsonPropertyName("is_matched")]
    public bool IsMatched { get; set; }

    [JsonPropertyName("match_type")]
    public string MatchType { get; set; } = "none";

    [JsonPropertyName("similarity_score")]
    public double SimilarityScore { get; set; }

    [JsonPropertyName("source_doc")]
    public string? SourceDoc { get; set; }

    [JsonPropertyName("source_page")]
    public int? SourcePage { get; set; }

    [JsonPropertyName("source_chunk_id")]
    public string? SourceChunkId { get; set; }

    [JsonPropertyName("verbatim_span")]
    public string? VerbatimSpan { get; set; }
}

public class ClaimVerificationDto
{
    [JsonPropertyName("claim_id")]
    public string ClaimId { get; set; } = "";

    [JsonPropertyName("claim_text")]
    public string ClaimText { get; set; } = "";

    [JsonPropertyName("verdict")]
    public string Verdict { get; set; } = "UNSUPPORTED";

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("attribution")]
    public SpanMatchResultDto? Attribution { get; set; }

    [JsonPropertyName("audit_notes")]
    public string AuditNotes { get; set; } = "";

    [JsonIgnore]
    public string VerdictBadge => Verdict switch
    {
        "VERIFIED" => "✓ VERIFIED SPAN",
        "PARTIALLY_SUPPORTED" => "⚡ PARTIAL",
        _ => "⚠️ UNSUPPORTED"
    };

    [JsonIgnore]
    public bool IsVerified => Verdict == "VERIFIED";
}

public class ProofReportDto
{
    [JsonPropertyName("report_id")]
    public string ReportId { get; set; } = "";

    [JsonPropertyName("timestamp_utc")]
    public string TimestampUtc { get; set; } = "";

    [JsonPropertyName("total_claims")]
    public int TotalClaims { get; set; }

    [JsonPropertyName("verified_claims")]
    public int VerifiedClaims { get; set; }

    [JsonPropertyName("unsupported_claims")]
    public int UnsupportedClaims { get; set; }

    [JsonPropertyName("grounding_ratio")]
    public double GroundingRatio { get; set; }

    [JsonPropertyName("is_strictly_verified")]
    public bool IsStrictlyVerified { get; set; }

    [JsonPropertyName("original_text")]
    public string OriginalText { get; set; } = "";

    [JsonPropertyName("verified_text")]
    public string VerifiedText { get; set; } = "";

    [JsonPropertyName("claims")]
    public List<ClaimVerificationDto> Claims { get; set; } = new();
}

public class ProverResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("proof_report")]
    public ProofReportDto? ProofReport { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

// ========================================================
// SUBSYSTEM 4: HIDDEN DISCOVERY & ISOMORPHISM DTOs
// ========================================================

public class DiscoveryCandidateDto
{
    [JsonPropertyName("target_entity")]
    public string TargetEntity { get; set; } = "";

    [JsonPropertyName("discovery_score")]
    public double DiscoveryScore { get; set; }

    [JsonPropertyName("bridging_mechanisms")]
    public List<string> BridgingMechanisms { get; set; } = new();

    [JsonPropertyName("path_count")]
    public int PathCount { get; set; }

    [JsonPropertyName("confidence_tier")]
    public string ConfidenceTier { get; set; } = "HIGH";

    [JsonPropertyName("rationale")]
    public string Rationale { get; set; } = "";

    [JsonIgnore]
    public string BridgesSummary => BridgingMechanisms.Count > 0 ? string.Join(", ", BridgingMechanisms) : "Direct Triad";
}

public class SwansonReportDto
{
    [JsonPropertyName("mode")]
    public string Mode { get; set; } = "open_discovery";

    [JsonPropertyName("source_entity")]
    public string SourceEntity { get; set; } = "";

    [JsonPropertyName("target_entity")]
    public string? TargetEntity { get; set; }

    [JsonPropertyName("total_triads_evaluated")]
    public int TotalTriadsEvaluated { get; set; }

    [JsonPropertyName("candidates")]
    public List<DiscoveryCandidateDto> Candidates { get; set; } = new();

    [JsonPropertyName("bridges_found")]
    public List<string> BridgesFound { get; set; } = new();
}

public class SwansonResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("report")]
    public SwansonReportDto? Report { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

public class EquationNodeDto
{
    [JsonPropertyName("equation_id")]
    public string EquationId { get; set; } = "";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("raw_expression")]
    public string RawExpression { get; set; } = "";

    [JsonPropertyName("domain")]
    public string Domain { get; set; } = "";

    [JsonPropertyName("source_doc")]
    public string? SourceDoc { get; set; }

    [JsonPropertyName("canonical_form")]
    public string CanonicalForm { get; set; } = "";

    [JsonPropertyName("ast_signature")]
    public string AstSignature { get; set; } = "";
}

public class IsomorphismClusterDto
{
    [JsonPropertyName("cluster_id")]
    public string ClusterId { get; set; } = "";

    [JsonPropertyName("ast_signature")]
    public string AstSignature { get; set; } = "";

    [JsonPropertyName("domains_involved")]
    public List<string> DomainsInvolved { get; set; } = new();

    [JsonPropertyName("equations")]
    public List<EquationNodeDto> Equations { get; set; } = new();

    [JsonPropertyName("analogy_description")]
    public string AnalogyDescription { get; set; } = "";

    [JsonIgnore]
    public string DomainsSummary => string.Join(" ⟷ ", DomainsInvolved);
}

public class IsomorphismReportDto
{
    [JsonPropertyName("total_equations_indexed")]
    public int TotalEquationsIndexed { get; set; }

    [JsonPropertyName("total_isomorphic_clusters")]
    public int TotalIsomorphicClusters { get; set; }

    [JsonPropertyName("cross_domain_discoveries")]
    public List<IsomorphismClusterDto> CrossDomainDiscoveries { get; set; } = new();
}

public class IsomorphismResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("report")]
    public IsomorphismReportDto? Report { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}

// ========================================================
// SUBSYSTEM 8: GENERATIVE CAD & FEA SIMULATION DTOs
// ========================================================

public class CadScriptResultDto
{
    [JsonPropertyName("is_safe")]
    public bool IsSafe { get; set; }

    [JsonPropertyName("script_code")]
    public string ScriptCode { get; set; } = "";

    [JsonPropertyName("component_type")]
    public string ComponentType { get; set; } = "";

    [JsonPropertyName("features")]
    public List<string> Features { get; set; } = new();

    [JsonPropertyName("syntax_valid")]
    public bool SyntaxValid { get; set; }

    [JsonPropertyName("error_message")]
    public string? ErrorMessage { get; set; }
}

public class GeometryValidationDto
{
    [JsonPropertyName("is_valid")]
    public bool IsValid { get; set; }

    [JsonPropertyName("volume_mm3")]
    public double VolumeMm3 { get; set; }

    [JsonPropertyName("is_manifold")]
    public bool IsManifold { get; set; }

    [JsonPropertyName("has_positive_volume")]
    public bool HasPositiveVolume { get; set; }
}

public class FEAResultDto
{
    [JsonPropertyName("material_used")]
    public string MaterialUsed { get; set; } = "";

    [JsonPropertyName("applied_load_n")]
    public double AppliedLoadN { get; set; }

    [JsonPropertyName("max_von_mises_stress_mpa")]
    public double MaxVonMisesStressMpa { get; set; }

    [JsonPropertyName("yield_strength_mpa")]
    public double YieldStrengthMpa { get; set; }

    [JsonPropertyName("factor_of_safety")]
    public double FactorOfSafety { get; set; }

    [JsonPropertyName("max_deflection_mm")]
    public double MaxDeflectionMm { get; set; }

    [JsonPropertyName("is_structurally_safe")]
    public bool IsStructurallySafe { get; set; }

    [JsonPropertyName("summary")]
    public string Summary { get; set; } = "";
}

public class CadGenerateResponseDto
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("cad_script")]
    public CadScriptResultDto? CadScript { get; set; }

    [JsonPropertyName("geometry_validation")]
    public GeometryValidationDto? GeometryValidation { get; set; }

    [JsonPropertyName("fea_simulation")]
    public FEAResultDto? FeaSimulation { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }
}


