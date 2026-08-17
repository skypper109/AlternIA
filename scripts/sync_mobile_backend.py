import os
from pathlib import Path

MOBILE_DIR = Path("/Users/ibrahimsorydiallo/Desktop/OSC/det-mobile")

# 1. Update device_repository.dart
DEVICE_REPO = '''// ─── DetAI — Feature: Device — Repository (Interface + Impl) ─────────────────
// Interface domain + implémentation data : scan Wi-Fi, connexion WebSocket.
library;

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:fpdart/fpdart.dart';
import 'package:logger/logger.dart';

import '../../core/failures.dart';
import '../../core/ws_manager.dart';
import 'device_entity.dart';

// ══════════════════════════════════════════════════════════════════════════════
// INTERFACE (DOMAIN)
// ══════════════════════════════════════════════════════════════════════════════

abstract interface class IDeviceRepository {
  Future<DetResult<List<DeviceEntity>>> scanDevices();
  Future<DetResult<DeviceEntity>> connectToDevice(DeviceEntity device);
  Future<DetVoidResult> disconnectDevice();
  Stream<WsConnectionState> watchConnectionState();
}

// ══════════════════════════════════════════════════════════════════════════════
// IMPLÉMENTATION (DATA)
// ══════════════════════════════════════════════════════════════════════════════

class DeviceRepository implements IDeviceRepository {
  DeviceRepository({
    required DetWebSocketManager wsManager,
    Dio? dio,
    this.detectorPort = 8000,
    this.scanTimeout  = const Duration(seconds: 3),
  })  : _wsManager = wsManager,
        _dio = dio ?? Dio(BaseOptions(connectTimeout: const Duration(seconds: 2)));

  final DetWebSocketManager _wsManager;
  final Dio                 _dio;
  final int                 detectorPort;
  final Duration            scanTimeout;
  final _logger = Logger();

  static final geminiVirtualDevice = DeviceEntity(
    id: 'alternia-local-server',
    name: 'Boîtier AlternIA (Local AI & RAG Mali)',
    ipAddress: '127.0.0.1',
    port: 8000,
    signalStrength: -30,
    firmwareVersion: 'v2.0-LocalEdge',
    lastSeen: DateTime.now(),
  );

  // ── Scan réseau ──────────────────────────────────────────────────────────

  @override
  Future<DetResult<List<DeviceEntity>>> scanDevices() async {
    try {
      final candidates = _buildCandidateList();
      _logger.i('[Device] Scan de ${candidates.length} adresses…');

      final futures = candidates.map((ip) => _probeDevice(ip));
      final results = await Future.wait(futures, eagerError: false);

      final found = results.whereType<DeviceEntity>().toList();
      final devices = [geminiVirtualDevice, ...found];
      _logger.i('[Device] ${devices.length} boîtier(s) disponible(s)');

      return right(devices);
    } catch (e, st) {
      _logger.e('[Device] Erreur scan, retour serveur Gemini', error: e, stackTrace: st);
      return right([geminiVirtualDevice]);
    }
  }

  List<String> _buildCandidateList() {
    return [
      '127.0.0.1',
      'localhost',
      '10.0.2.2',
      '192.168.4.1',
      '192.168.1.1',
      '10.42.0.1',
      '172.16.0.1',
    ];
  }

  Future<DeviceEntity?> _probeDevice(String ip) async {
    for (final port in [8000, 8080]) {
      try {
        final response = await _dio.get(
          'http://$ip:$port/api/info',
          options: Options(
            receiveTimeout: const Duration(seconds: 2),
            sendTimeout:    const Duration(seconds: 2),
          ),
        );

        if (response.statusCode == 200 && response.data is Map) {
          return _parseDeviceInfo(ip, port, response.data as Map<String, dynamic>);
        }
      } catch (_) {}
    }
    return null;
  }

  DeviceEntity _parseDeviceInfo(String ip, int port, Map<String, dynamic> data) {
    return DeviceEntity(
      id:              data['device_id'] as String? ?? data['id'] as String? ?? ip,
      name:            data['device_name'] as String? ?? data['name'] as String? ?? 'Boîtier AlternIA',
      ipAddress:       ip,
      port:            port,
      firmwareVersion: data['firmware'] as String? ?? data['firmware_version'] as String? ?? 'v2.0',
      lastSeen:        DateTime.now(),
    );
  }

  // ── Connexion WebSocket ───────────────────────────────────────────────────

  @override
  Future<DetResult<DeviceEntity>> connectToDevice(DeviceEntity device) async {
    try {
      final wsTarget = 'ws://${device.ipAddress}:${device.port}/ws/session';
      await _wsManager.connect(wsTarget);
      _logger.i('[Device] Connexion WS à $wsTarget');
      return right(device.copyWith(isConnected: true));
    } catch (e) {
      _logger.e('[Device] Échec connexion : $e');
      return left(DeviceConnectionFailure());
    }
  }

  @override
  Future<DetVoidResult> disconnectDevice() async {
    try {
      await _wsManager.disconnect();
      return right(unit);
    } catch (e) {
      return left(DeviceConnectionFailure(
        message: 'Erreur lors de la déconnexion : $e',
      ));
    }
  }

  @override
  Stream<WsConnectionState> watchConnectionState() =>
      _wsManager.stateStream;
}
'''

with open(MOBILE_DIR / "lib/features/device/device_repository.dart", "w", encoding="utf-8") as f:
    f.write(DEVICE_REPO)
print("✅ Updated device_repository.dart")

# 2. Update progress_repository.dart
PROGRESS_REPO = '''// ─── DetAI — Feature: Progress — Repository + Notifier + Page ─────────────────
// Persistance locale & synchronisation temps réel avec le backend AlternIA.
library;

import 'dart:io' show Platform;
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants.dart';
import '../../shared/painters.dart';
import '../../shared/widgets.dart';
import 'progress_entity.dart';

part 'progress_repository.g.dart';

// ══════════════════════════════════════════════════════════════════════════════
// REPOSITORY (Connecté à l'API Backend AlternIA)
// ══════════════════════════════════════════════════════════════════════════════

class ProgressRepository {
  ProgressRepository({required SharedPreferences prefs, Dio? dio})
      : _dio = dio ?? Dio(BaseOptions(connectTimeout: const Duration(seconds: 4)));

  final Dio _dio;
  final _logger = Logger();

  List<String> get _candidateBaseUrls {
    if (kIsWeb) return ['http://127.0.0.1:8000', 'http://localhost:8000'];
    try {
      if (Platform.isAndroid) {
        return [
          'http://10.0.2.2:8000',
          'http://127.0.0.1:8000',
          'http://192.168.4.1:8000',
        ];
      }
    } catch (_) {}
    return [
      'http://127.0.0.1:8000',
      'http://localhost:8000',
      'http://192.168.4.1:8000',
    ];
  }

  /// Charge les données radar depuis le backend AlternIA
  Future<List<CompetencyRadar>> loadRadarData() async {
    for (final url in _candidateBaseUrls) {
      try {
        final res = await _dio.get('$url/api/parent/progression');
        if (res.statusCode == 200 && res.data is Map) {
          final data = res.data as Map<String, dynamic>;
          final matieres = data['matieres'] as List<dynamic>? ?? [];
          if (matieres.isNotEmpty) {
            final mathEntries = <CompetencyEntry>[];
            final pcEntries = <CompetencyEntry>[];

            for (final m in matieres) {
              final nom = (m['matiere'] as String? ?? '');
              final scorePct = ((m['score'] as num?)?.toDouble() ?? 70.0) / 100.0;
              final notion = (m['notion'] as String? ?? nom);

              if (nom.toLowerCase().contains('math')) {
                mathEntries.add(CompetencyEntry(name: notion, score: scorePct, sessionCount: 6));
              } else {
                pcEntries.add(CompetencyEntry(name: notion, score: scorePct, sessionCount: 5));
              }
            }

            if (mathEntries.isNotEmpty || pcEntries.isNotEmpty) {
              return [
                CompetencyRadar(
                  subject: 'Mathématiques',
                  entries: mathEntries.isNotEmpty ? mathEntries : demoRadarData[0].entries,
                  updatedAt: DateTime.now(),
                ),
                CompetencyRadar(
                  subject: 'Sciences & Physique',
                  entries: pcEntries.isNotEmpty ? pcEntries : demoRadarData[1].entries,
                  updatedAt: DateTime.now(),
                ),
              ];
            }
          }
        }
      } catch (e) {
        _logger.w('[ProgressRepo] Backend inaccessible sur $url : $e');
      }
    }
    return demoRadarData;
  }

  /// Charge l'historique des sessions depuis le backend AlternIA
  Future<List<ProgressEntry>> loadHistory() async {
    for (final url in _candidateBaseUrls) {
      try {
        final res = await _dio.get('$url/api/parent/historique');
        if (res.statusCode == 200 && res.data is List) {
          final list = res.data as List<dynamic>;
          return list.map((item) {
            final m = item as Map<String, dynamic>;
            return ProgressEntry(
              id: m['id'] as String? ?? DateTime.now().toIso8601String(),
              subject: m['matiere'] as String? ?? 'Général',
              date: m['date'] != null ? DateTime.tryParse(m['date'] as String) ?? DateTime.now() : DateTime.now(),
              durationMinutes: (m['dureeMinutes'] as num?)?.toInt() ?? 30,
              hintsUsed: (m['questionsPosees'] as num?)?.toInt() ?? 4,
              progressScore: ((m['score'] as num?)?.toDouble() ?? 80.0) / 100.0,
              notes: m['resume'] as String? ?? m['notion'] as String?,
            );
          }).toList();
        }
      } catch (_) {}
    }
    return [
      ProgressEntry(
        id: 'ses-01',
        subject: 'SVT / Biologie',
        date: DateTime.now(),
        durationMinutes: 25,
        hintsUsed: 3,
        progressScore: 0.88,
        notes: 'Session sur la zonation végétale et facteurs sahéliens.',
      ),
      ProgressEntry(
        id: 'ses-02',
        subject: 'Mathématiques',
        date: DateTime.now().subtract(const Duration(days: 1)),
        durationMinutes: 35,
        hintsUsed: 5,
        progressScore: 0.75,
        notes: 'Équations du 2nd degré et méthode du discriminant.',
      ),
    ];
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// PROVIDER
// ══════════════════════════════════════════════════════════════════════════════

@Riverpod(keepAlive: true)
Future<SharedPreferences> sharedPreferences(Ref ref) =>
    SharedPreferences.getInstance();

@Riverpod(keepAlive: true)
Future<ProgressRepository> progressRepository(Ref ref) async {
  final prefs = await ref.watch(sharedPreferencesProvider.future);
  return ProgressRepository(prefs: prefs);
}

// ══════════════════════════════════════════════════════════════════════════════
// NOTIFIER
// ══════════════════════════════════════════════════════════════════════════════

@riverpod
class ProgressNotifier extends _$ProgressNotifier {
  @override
  Future<ProgressState> build() async {
    final repo = await ref.watch(progressRepositoryProvider.future);

    final radars = await repo.loadRadarData();
    final history = await repo.loadHistory();

    return ProgressState(radars: radars, history: history);
  }

  /// Force un rechargement des données.
  Future<void> refresh() async => ref.invalidateSelf();
}

/// État interne de la feature Progress.
class ProgressState {
  const ProgressState({required this.radars, required this.history});
  final List<CompetencyRadar> radars;
  final List<ProgressEntry> history;
}

// ══════════════════════════════════════════════════════════════════════════════
// PAGE
// ══════════════════════════════════════════════════════════════════════════════

/// Écran du Carnet de Compétences avec graphiques radar.
class ProgressPage extends ConsumerStatefulWidget {
  const ProgressPage({super.key});

  @override
  ConsumerState<ProgressPage> createState() => _ProgressPageState();
}

class _ProgressPageState extends ConsumerState<ProgressPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final progressAsync = ref.watch(progressNotifierProvider);

    return Scaffold(
      backgroundColor: AltaColors.backgroundDark,
      body: SafeArea(
        child: Column(
          children: [
            // ── Header ─────────────────────────────────────────────────────
            _ProgressHeader(tabCtrl: _tabCtrl),

            // ── Contenu ────────────────────────────────────────────────────
            Expanded(
              child: progressAsync.when(
                loading: () => const Center(child: CircularProgressIndicator(color: AltaColors.primary)),
                error: (e, _) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('Erreur de chargement : $e', style: const TextStyle(color: AltaColors.error)),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () => ref.read(progressNotifierProvider.notifier).refresh(),
                          child: const Text('Réessayer'),
                        ),
                      ],
                    ),
                  ),
                ),
                data: (state) => TabBarView(
                  controller: _tabCtrl,
                  children: [
                    _RadarTab(radars: state.radars),
                    _HistoryTab(history: state.history),
                    _StatsTab(history: state.history),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Header avec tabs ──────────────────────────────────────────────────────────

class _ProgressHeader extends StatelessWidget {
  const _ProgressHeader({required this.tabCtrl});
  final TabController tabCtrl;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: const BoxDecoration(
        color: AltaColors.surfaceDark,
        border: Border(bottom: BorderSide(color: AltaColors.borderDark)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Text('Carnet de Suivi', style: DetTextStyles.headingMd),
              Spacer(),
              AlterniaLogo(size: 28, showText: true),
            ],
          ),
          const SizedBox(height: 12),
          TabBar(
            controller: tabCtrl,
            indicatorColor: AltaColors.primary,
            labelColor: AltaColors.accent,
            unselectedLabelColor: AltaColors.textSecondaryDark,
            tabs: const [
              Tab(text: 'Compétences'),
              Tab(text: 'Historique'),
              Tab(text: 'Statistiques'),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Tab Radar ─────────────────────────────────────────────────────────────────

class _RadarTab extends StatelessWidget {
  const _RadarTab({required this.radars});
  final List<CompetencyRadar> radars;

  @override
  Widget build(BuildContext context) {
    if (radars.isEmpty) {
      return const Center(child: Text('Aucune donnée de compétence.', style: TextStyle(color: AltaColors.textSecondaryDark)));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: radars.length,
      itemBuilder: (context, idx) {
        final radar = radars[idx];
        final entries = radar.entries.map((e) => RadarEntry(label: e.name, value: e.score)).toList();

        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          color: AltaColors.surfaceDark,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: AltaColors.borderDark),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(radar.subject, style: DetTextStyles.headingSm),
                const SizedBox(height: 16),
                SizedBox(
                  height: 220,
                  width: double.infinity,
                  child: CustomPaint(
                    painter: RadarChartPainter(
                      entries: entries,
                      fillColor: AltaColors.primary.withValues(alpha: 0.25),
                      lineColor: AltaColors.secondary,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ── Tab Historique ────────────────────────────────────────────────────────────

class _HistoryTab extends StatelessWidget {
  const _HistoryTab({required this.history});
  final List<ProgressEntry> history;

  @override
  Widget build(BuildContext context) {
    if (history.isEmpty) {
      return const Center(child: Text('Aucune session enregistrée.', style: TextStyle(color: AltaColors.textSecondaryDark)));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(20),
      itemCount: history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, idx) {
        final item = history[idx];
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AltaColors.surfaceDark,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AltaColors.borderDark),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AltaColors.primary.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.school_rounded, color: AltaColors.secondary, size: 20),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.subject, style: DetTextStyles.bodyMd.copyWith(fontWeight: FontWeight.bold)),
                    if (item.notes != null)
                      Text(item.notes!, style: DetTextStyles.bodySm.copyWith(color: AltaColors.textSecondaryDark)),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('${(item.progressScore * 100).toInt()}%', style: DetTextStyles.bodyMd.copyWith(color: AltaColors.success, fontWeight: FontWeight.bold)),
                  Text('${item.durationMinutes} min', style: DetTextStyles.caption.copyWith(color: AltaColors.textMutedDark)),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── Tab Statistiques ──────────────────────────────────────────────────────────

class _StatsTab extends StatelessWidget {
  const _StatsTab({required this.history});
  final List<ProgressEntry> history;

  @override
  Widget build(BuildContext context) {
    final totalMin = history.fold<int>(0, (sum, item) => sum + item.durationMinutes);
    final avgScore = history.isEmpty
        ? 0
        : (history.fold<double>(0, (sum, item) => sum + item.progressScore) / history.length * 100).toInt();

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Row(
          children: [
            Expanded(
              child: _StatCard(
                label: 'Temps total',
                value: '$totalMin min',
                icon: Icons.timer_rounded,
                color: AltaColors.primary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatCard(
                label: 'Score moyen',
                value: '$avgScore%',
                icon: Icons.auto_graph_rounded,
                color: AltaColors.success,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.icon, required this.color});
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AltaColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AltaColors.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 10),
          Text(value, style: DetTextStyles.headingMd),
          Text(label, style: DetTextStyles.caption.copyWith(color: AltaColors.textSecondaryDark)),
        ],
      ),
    );
  }
}
'''

with open(MOBILE_DIR / "lib/features/progress/progress_repository.dart", "w", encoding="utf-8") as f:
    f.write(PROGRESS_REPO)
print("✅ Updated progress_repository.dart")

# 3. Update documents_page.dart
DOCUMENTS_PAGE = '''// ─── AlterniA — Feature: Documents & Scanner Socratique ──────────────────────
// Import et analyse socratique d'exercices connecté au moteur RAG AlternIA.
library;

import 'dart:io' show Platform;
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/constants.dart';
import '../../shared/widgets.dart';
import '../profile/user_prefs_notifier.dart';

class DocumentsPage extends ConsumerStatefulWidget {
  const DocumentsPage({super.key});

  @override
  ConsumerState<DocumentsPage> createState() => _DocumentsPageState();
}

class _DocumentsPageState extends ConsumerState<DocumentsPage>
    with SingleTickerProviderStateMixin {
  bool _isProcessing = false;
  int _currentStep = 0;
  String? _scannedFileName;
  late final AnimationController _pulseCtrl;

  final List<_DocHistory> _history = [
    _DocHistory(
      name: 'Exercice_Maths_Intégrales.pdf',
      subject: 'Mathématiques',
      date: 'Hier • 14:32',
      steps: 4,
      color: AltaColors.primary,
    ),
    _DocHistory(
      name: 'Devoir_Physique_Newton.jpg',
      subject: 'Physique',
      date: 'Il y a 2 jours',
      steps: 4,
      color: AltaColors.accent,
    ),
    _DocHistory(
      name: 'Cours_SVT_Mitose.pdf',
      subject: 'Sciences Naturelles',
      date: 'Il y a 5 jours',
      steps: 4,
      color: AltaColors.secondary,
    ),
  ];

  List<Map<String, String>> _socraticSteps = [
    {
      'title': 'Étape 1 • Observons l\\'énoncé',
      'content': 'Analyse RAG réalisée avec succès. AlterniA a identifié le type d\\'exercice et les données clés du problème.',
      'question': 'Quelle est la première donnée importante que tu remarques dans l\\'énoncé ?',
    },
    {
      'title': 'Étape 2 • Que comprends-tu ?',
      'content': 'Avant d\\'appliquer une formule, il faut comprendre ce qu\\'on cherche. AlterniA t\\'accompagne dans cette réflexion.',
      'question': 'Quelle méthode ou formule du programme malien te semble appropriée ?',
    },
    {
      'title': 'Étape 3 • Essayons ensemble',
      'content': 'AlterniA te guide pas à pas. Chaque étape de raisonnement compte autant que la réponse finale.',
      'question': 'Que vaut le résultat intermédiaire après cette première simplification ?',
    },
    {
      'title': 'Étape 4 • Validation de la méthode',
      'content': 'Excellent travail ! Vérifions ensemble que la solution est cohérente avec les données de départ.',
      'question': 'As-tu bien compris chaque étape de la méthode ?',
    },
  ];

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  List<String> get _candidateBaseUrls {
    if (kIsWeb) return ['http://127.0.0.1:8000', 'http://localhost:8000'];
    try {
      if (Platform.isAndroid) {
        return [
          'http://10.0.2.2:8000',
          'http://127.0.0.1:8000',
          'http://192.168.4.1:8000',
        ];
      }
    } catch (_) {}
    return [
      'http://127.0.0.1:8000',
      'http://localhost:8000',
      'http://192.168.4.1:8000',
    ];
  }

  Future<void> _importDocument(String type) async {
    final userPrefs = ref.read(userPrefsProvider);
    HapticFeedback.mediumImpact();
    setState(() {
      _isProcessing = true;
      _scannedFileName = 'Document_${userPrefs.classShortLabel}_$type.pdf';
    });

    final dio = Dio();
    bool success = false;

    for (final url in _candidateBaseUrls) {
      try {
        final formData = FormData.fromMap({
          'subject': 'Sciences & Mathématiques',
          'level': userPrefs.studentClassId,
          'text': 'Analyse d\\'exercice scolaire du programme malien',
        });

        final res = await dio.post(
          '$url/api/rag/analyze',
          data: formData,
          options: Options(connectTimeout: const Duration(seconds: 4), receiveTimeout: const Duration(seconds: 8)),
        );

        if (res.statusCode == 200 && res.data is Map) {
          final hints = (res.data['hints'] as List<dynamic>? ?? []);
          if (hints.isNotEmpty) {
            final parsedSteps = <Map<String, String>>[];
            for (var i = 0; i < hints.length; i++) {
              final h = hints[i] as Map<String, dynamic>;
              parsedSteps.add({
                'title': 'Étape ${i + 1} • ${(h['type'] as String? ?? 'Raisonnement').toUpperCase()}',
                'content': h['text'] as String? ?? h['content'] as String? ?? 'Analyse en cours.',
                'question': h['question'] as String? ?? 'Quelle est ton hypothèse pour cette étape ?',
              });
            }
            if (mounted) {
              setState(() {
                _socraticSteps = parsedSteps;
                _isProcessing = false;
                _currentStep = 0;
              });
            }
            success = true;
            break;
          }
        }
      } catch (_) {}
    }

    if (!success && mounted) {
      setState(() {
        _isProcessing = false;
        _currentStep = 0;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? AltaColors.surfaceDark : AltaColors.surfaceLight;
    final borderCol = isDark ? AltaColors.borderDark : AltaColors.borderLight;
    final textPri = isDark ? AltaColors.textPrimaryDark : AltaColors.textPrimaryLight;
    final textSec = isDark ? AltaColors.textSecondaryDark : AltaColors.textSecondaryLight;
    final userPrefs = ref.watch(userPrefsProvider);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 100),
          children: [
            // ── En-tête ─────────────────────────────────────────────────────
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'MES DOCUMENTS',
                      style: DetTextStyles.caption.copyWith(
                        color: AltaColors.accent,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Scanner Socratique',
                      style: DetTextStyles.displayMd.copyWith(
                        color: textPri,
                      ),
                    ),
                  ],
                ),
                const AlterniaLogo(size: 28, showText: true),
              ],
            ),

            const SizedBox(height: DetSizes.xl),

            // ── Zone d'importation ──────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(DetSizes.xl),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AltaColors.primary.withValues(alpha: isDark ? 0.2 : 0.08),
                    AltaColors.secondary.withValues(alpha: isDark ? 0.1 : 0.05),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: DetSizes.borderRadiusXl,
                border: Border.all(
                  color: AltaColors.primary.withValues(alpha: 0.4),
                  width: DetSizes.borderWidth,
                ),
              ),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(DetSizes.lg),
                    decoration: BoxDecoration(
                      color: AltaColors.primary.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.document_scanner_rounded,
                      size: 40,
                      color: AltaColors.primary,
                    ),
                  ),
                  const SizedBox(height: DetSizes.md),
                  Text(
                    'Importer un exercice',
                    style: DetTextStyles.headingMd.copyWith(color: textPri),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'AlterniA analyse votre devoir et vous guide pas à pas.',
                    textAlign: TextAlign.center,
                    style: DetTextStyles.bodySm.copyWith(color: textSec),
                  ),
                  const SizedBox(height: DetSizes.lg),
                  Row(
                    children: [
                      Expanded(
                        child: DetButton(
                          label: 'Caméra',
                          icon: Icons.camera_alt_rounded,
                          onPressed: () => _importDocument('Photo'),
                        ),
                      ),
                      const SizedBox(width: DetSizes.md),
                      Expanded(
                        child: DetButton(
                          label: 'Galerie',
                          icon: Icons.photo_library_rounded,
                          variant: DetButtonVariant.secondary,
                          onPressed: () => _importDocument('Galerie'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: DetSizes.xl),

            // ── Résultat de l'analyse ou Chargement ──────────────────────────
            if (_isProcessing) ...[
              Container(
                padding: const EdgeInsets.all(DetSizes.xl),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: DetSizes.borderRadiusLg,
                  border: Border.all(color: borderCol),
                ),
                child: Column(
                  children: [
                    AnimatedBuilder(
                      animation: _pulseCtrl,
                      builder: (context, child) {
                        return Transform.scale(
                          scale: 0.95 + 0.1 * _pulseCtrl.value,
                          child: Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: AltaColors.secondary.withValues(alpha: 0.2),
                              border: Border.all(
                                color: AltaColors.secondary,
                                width: 2,
                              ),
                            ),
                            child: const Icon(
                              Icons.psychology_rounded,
                              color: AltaColors.secondary,
                              size: 32,
                            ),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: DetSizes.md),
                    Text(
                      'Analyse Socratique par AlterniA…',
                      style: DetTextStyles.headingSm.copyWith(color: textPri),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Recherche des concepts du programme (${userPrefs.classFullLabel})',
                      style: DetTextStyles.bodySm.copyWith(color: textSec),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: DetSizes.xl),
            ] else if (_scannedFileName != null) ...[
              Container(
                padding: const EdgeInsets.all(DetSizes.lg),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: DetSizes.borderRadiusLg,
                  border: Border.all(
                    color: AltaColors.secondary.withValues(alpha: 0.5),
                    width: 1.5,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.check_circle_rounded,
                          color: AltaColors.secondary,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _scannedFileName!,
                            style: DetTextStyles.bodyMd.copyWith(
                              color: textPri,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    Text(
                      _socraticSteps[_currentStep]['title']!,
                      style: DetTextStyles.headingSm.copyWith(
                        color: AltaColors.accent,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _socraticSteps[_currentStep]['content']!,
                      style: DetTextStyles.bodyMd.copyWith(
                        color: textPri,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(DetSizes.md),
                      decoration: BoxDecoration(
                        color: AltaColors.primary.withValues(alpha: isDark ? 0.15 : 0.06),
                        borderRadius: DetSizes.borderRadiusMd,
                        border: Border.all(
                          color: AltaColors.primary.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(
                            Icons.help_outline_rounded,
                            color: AltaColors.primary,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _socraticSteps[_currentStep]['question']!,
                              style: DetTextStyles.bodySm.copyWith(
                                color: textPri,
                                fontStyle: FontStyle.italic,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: DetSizes.md),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        if (_currentStep > 0)
                          TextButton.icon(
                            onPressed: () {
                              setState(() => _currentStep--);
                            },
                            icon: const Icon(Icons.arrow_back_rounded, size: 16),
                            label: const Text('Précédent'),
                          )
                        else
                          const SizedBox.shrink(),
                        if (_currentStep < _socraticSteps.length - 1)
                          DetButton(
                            label: 'Étape suivante',
                            icon: Icons.arrow_forward_rounded,
                            onPressed: () {
                              setState(() => _currentStep++);
                            },
                          )
                        else
                          DetButton(
                            label: 'Terminer',
                            icon: Icons.done_all_rounded,
                            variant: DetButtonVariant.secondary,
                            onPressed: () {
                              setState(() {
                                _scannedFileName = null;
                                _currentStep = 0;
                              });
                            },
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: DetSizes.xl),
            ],

            // ── Historique des devoirs ──────────────────────────────────────
            Text(
              'HISTORIQUE DES ANALYSES',
              style: DetTextStyles.caption.copyWith(
                color: AltaColors.accent,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: DetSizes.md),
            ..._history.map((doc) => Padding(
              padding: const EdgeInsets.only(bottom: DetSizes.sm),
              child: _DocHistoryCard(doc: doc),
            )),
          ],
        ),
      ),
    );
  }
}

class _DocHistory {
  _DocHistory({
    required this.name,
    required this.subject,
    required this.date,
    required this.steps,
    required this.color,
  });

  final String name;
  final String subject;
  final String date;
  final int steps;
  final Color color;
}

class _DocHistoryCard extends StatelessWidget {
  const _DocHistoryCard({required this.doc});
  final _DocHistory doc;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? AltaColors.surfaceDark : AltaColors.surfaceLight;
    final borderCol = isDark ? AltaColors.borderDark : AltaColors.borderLight;
    final textPri = isDark ? AltaColors.textPrimaryDark : AltaColors.textPrimaryLight;
    final textSec = isDark ? AltaColors.textSecondaryDark : AltaColors.textSecondaryLight;

    return Container(
      padding: const EdgeInsets.all(DetSizes.md),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: DetSizes.borderRadiusMd,
        border: Border.all(color: borderCol),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: doc.color.withValues(alpha: isDark ? 0.2 : 0.1),
              borderRadius: DetSizes.borderRadiusSm,
            ),
            child: Icon(Icons.picture_as_pdf_rounded, color: doc.color, size: 22),
          ),
          const SizedBox(width: DetSizes.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  doc.name,
                  style: DetTextStyles.bodyMd.copyWith(
                    color: textPri,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${doc.subject} • ${doc.date}',
                  style: DetTextStyles.caption.copyWith(color: textSec),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: AltaColors.secondary.withValues(alpha: isDark ? 0.2 : 0.1),
              borderRadius: DetSizes.borderRadiusSm,
            ),
            child: Text(
              '${doc.steps} étapes',
              style: DetTextStyles.caption.copyWith(
                color: AltaColors.secondary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
'''

with open(MOBILE_DIR / "lib/features/documents/documents_page.dart", "w", encoding="utf-8") as f:
    f.write(DOCUMENTS_PAGE)
print("✅ Updated documents_page.dart")
