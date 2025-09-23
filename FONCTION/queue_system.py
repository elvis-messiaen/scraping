#!/usr/bin/env python3
"""
SYSTÈME DE QUEUE ASYNC ULTRA-RAPIDE
===================================
Gestionnaire de queues pour scraping massif parallèle
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    """Représente une tâche dans la queue"""
    id: str
    type: str
    data: Dict[str, Any]
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

class AsyncQueueManager:
    """
    Gestionnaire de queues async ultra-performant
    """

    def __init__(self, max_concurrent_tasks=100, max_queue_size=10000):
        self.max_concurrent = max_concurrent_tasks
        self.max_queue_size = max_queue_size
        self.ssl_errors_count = 0  # Compteur d'erreurs SSL

        # Queues et semaphores seront créés dans le bon event loop
        self.queues = {}
        self.semaphores = {}
        self.queues_initialized = False

        # Tracking des tâches
        self.tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}

        # Statistiques
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'processing_times': []
        }

        # Workers
        self.workers = {}
        self.running = False

    async def _initialize_queues(self):
        """Initialise les queues et semaphores dans le bon event loop"""
        if not self.queues_initialized:
            print("🔧 Initialisation des queues async...")

            # Créer queues dans le bon event loop
            self.queues = {
                'descriptions': asyncio.Queue(maxsize=self.max_queue_size),
                'pages': asyncio.Queue(maxsize=self.max_queue_size),
                'sauvegarde': asyncio.Queue(maxsize=self.max_queue_size),
            }

            # Créer semaphores dans le bon event loop
            self.semaphores = {
                'descriptions': asyncio.Semaphore(self.max_concurrent),
                'pages': asyncio.Semaphore(10),  # Moins de pages simultanées
                'sauvegarde': asyncio.Semaphore(5),  # Limite pour sauvegarde
            }

            self.queues_initialized = True
            print("✅ Queues initialisées")

    async def add_task(self, task_type: str, task_data: Dict[str, Any], task_id: str = None) -> str:
        """Ajoute une tâche à la queue"""
        # Initialiser queues si nécessaire
        await self._initialize_queues()

        if task_id is None:
            task_id = f"{task_type}_{int(time.time() * 1000000)}"

        task = Task(
            id=task_id,
            type=task_type,
            data=task_data,
            status=TaskStatus.PENDING,
            created_at=time.time()
        )

        self.tasks[task_id] = task
        self.stats['total_tasks'] += 1

        await self.queues[task_type].put(task)
        return task_id

    async def add_batch_tasks(self, task_type: str, batch_data: List[Dict[str, Any]]) -> List[str]:
        """Ajoute un lot de tâches"""
        task_ids = []

        print(f"📋 Ajout batch: {len(batch_data)} tâches de type '{task_type}'")

        for i, data in enumerate(batch_data):
            task_id = await self.add_task(task_type, data)
            task_ids.append(task_id)

            # Log de progression
            if (i + 1) % 100 == 0:
                print(f"   📝 {i + 1}/{len(batch_data)} tâches ajoutées...")

        return task_ids

    async def start_workers(self):
        """Démarre les workers pour traiter les queues"""
        print(f"🚀 DÉMARRAGE WORKERS: {self.max_concurrent} workers max")

        self.running = True
        self.stats['start_time'] = time.time()

        # Créer workers pour chaque type de queue
        self.workers = {
            'descriptions': [
                asyncio.create_task(self._worker_descriptions(f"desc_{i}"))
                for i in range(self.max_concurrent)
            ],
            'pages': [
                asyncio.create_task(self._worker_pages(f"page_{i}"))
                for i in range(10)
            ],
            'sauvegarde': [
                asyncio.create_task(self._worker_sauvegarde(f"save_{i}"))
                for i in range(5)
            ]
        }

        print(f"✅ Workers démarrés: {sum(len(workers) for workers in self.workers.values())} workers actifs")

    async def stop_workers(self):
        """Arrête tous les workers"""
        print("🛑 Arrêt des workers...")
        self.running = False

        # Annuler tous les workers
        for worker_type, workers in self.workers.items():
            for worker in workers:
                worker.cancel()

        # Attendre l'arrêt
        await asyncio.sleep(1)
        print("✅ Workers arrêtés")

    async def wait_completion(self, timeout: float = None) -> bool:
        """Attend que toutes les tâches soient terminées"""
        start_time = time.time()
        last_completed = 0
        stalled_count = 0

        while self.running:
            # Vérifier si toutes les queues sont vides et tâches terminées
            total_pending = sum(queue.qsize() for queue in self.queues.values())
            total_processing = len([t for t in self.tasks.values() if t.status == TaskStatus.PROCESSING])
            current_completed = self.stats['completed_tasks']

            if total_pending == 0 and total_processing == 0:
                print("✅ Toutes les tâches terminées")
                return True

            # Détecter blocage des workers
            if current_completed == last_completed and total_processing == 0 and total_pending > 0:
                stalled_count += 1
                print(f"⚠️ Détection blocage: {stalled_count}/5 - Redémarrage workers...")

                if stalled_count >= 5:
                    print("🔄 REDÉMARRAGE FORCÉ DES WORKERS")
                    await self.stop_workers()
                    await self.start_workers()
                    stalled_count = 0
            else:
                stalled_count = 0
                last_completed = current_completed

            # Afficher progression
            await self._print_progress()

            # Vérifier timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"⏰ Timeout atteint ({timeout}s)")
                return False

            await asyncio.sleep(2)  # Check toutes les 2 secondes

        return True

    async def _worker_descriptions(self, worker_id: str):
        """Worker pour traitement des descriptions"""
        print(f"🔧 Worker {worker_id} démarré")

        try:
            from description_async import extraire_description_async
        except ImportError as e:
            print(f"❌ Erreur import description_async dans worker {worker_id}: {e}")
            return

        while self.running:
            try:
                # Attendre une tâche avec timeout
                task = await asyncio.wait_for(self.queues['descriptions'].get(), timeout=5.0)

                print(f"🔄 Worker {worker_id}: traitement {task.data.get('titre', 'Unknown')[:20]}...")

                # Acquérir semaphore et traiter la tâche
                async with self.semaphores['descriptions']:
                    await self._process_task(task, extraire_description_async)

            except asyncio.TimeoutError:
                # Pas de tâche disponible, continuer
                continue
            except Exception as e:
                print(f"❌ Erreur critique worker {worker_id}: {e}")
                # Attendre un peu avant de reprendre
                await asyncio.sleep(1)

        print(f"🛑 Worker {worker_id} arrêté")

    async def _worker_pages(self, worker_id: str):
        """Worker pour traitement des pages"""
        while self.running:
            try:
                async with self.semaphores['pages']:
                    task = await asyncio.wait_for(self.queues['pages'].get(), timeout=1.0)

                    # Traiter la page (à implémenter selon besoin)
                    await self._process_task(task, self._process_page)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Erreur worker {worker_id}: {e}")

    async def _worker_sauvegarde(self, worker_id: str):
        """Worker pour sauvegarde"""
        while self.running:
            try:
                async with self.semaphores['sauvegarde']:
                    task = await asyncio.wait_for(self.queues['sauvegarde'].get(), timeout=1.0)

                    # Traiter la sauvegarde
                    await self._process_task(task, self._process_sauvegarde)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Erreur worker {worker_id}: {e}")

    async def _process_task(self, task: Task, processor: Callable):
        """Traite une tâche avec gestion d'erreurs et retry"""
        task.status = TaskStatus.PROCESSING
        task.started_at = time.time()

        try:
            # Traitement spécifique selon le type
            if task.type == 'descriptions':
                result = await processor(task.data['url'], task.data.get('titre'))
            else:
                result = await processor(task.data)

            # Succès
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

            self.completed_tasks[task.id] = task
            self.stats['completed_tasks'] += 1
            self.stats['processing_times'].append(task.completed_at - task.started_at)

        except Exception as e:
            # Échec
            task.error = str(e)
            task.retries += 1

            if task.retries < task.max_retries:
                # Retry: remettre en queue
                task.status = TaskStatus.PENDING
                await self.queues[task.type].put(task)
            else:
                # Échec définitif
                task.status = TaskStatus.FAILED
                self.failed_tasks[task.id] = task
                self.stats['failed_tasks'] += 1

    async def _process_page(self, data: Dict[str, Any]):
        """Traitement d'une page (placeholder)"""
        await asyncio.sleep(0.1)  # Simulation
        return "page_processed"

    async def _process_sauvegarde(self, data: Dict[str, Any]):
        """Traitement sauvegarde (placeholder)"""
        await asyncio.sleep(0.1)  # Simulation
        return "saved"

    async def _print_progress(self):
        """Affiche la progression"""
        total = self.stats['total_tasks']
        completed = self.stats['completed_tasks']
        failed = self.stats['failed_tasks']
        processing = len([t for t in self.tasks.values() if t.status == TaskStatus.PROCESSING])
        pending = total - completed - failed - processing

        if total > 0:
            progress = (completed / total) * 100

            elapsed = time.time() - self.stats['start_time']
            rate = completed / elapsed if elapsed > 0 else 0

            print(f"📊 Progression: {progress:.1f}% | "
                  f"✅ {completed} | ❌ {failed} | 🔄 {processing} | ⏳ {pending} | "
                  f"⚡ {rate:.1f}/s")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        stats = self.stats.copy()

        if stats['processing_times']:
            stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
            stats['max_processing_time'] = max(stats['processing_times'])
            stats['min_processing_time'] = min(stats['processing_times'])

        if stats['start_time']:
            stats['total_elapsed'] = time.time() - stats['start_time']
            if stats['completed_tasks'] > 0:
                stats['overall_rate'] = stats['completed_tasks'] / stats['total_elapsed']

        return stats

# Instance globale avec concurrence réduite pour éviter erreurs SSL
queue_manager = AsyncQueueManager(max_concurrent_tasks=20)  # Réduit de 100 à 20

async def process_descriptions_batch(livres: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fonction principale pour traiter un batch de descriptions

    Args:
        livres: Liste de dicts avec au minimum 'url' et optionnellement 'titre'

    Returns:
        Liste des livres avec descriptions mises à jour
    """
    if not livres:
        return []

    print(f"🚀 TRAITEMENT BATCH ASYNC: {len(livres)} livres")

    # Ajouter toutes les tâches
    task_ids = await queue_manager.add_batch_tasks('descriptions', livres)

    # Démarrer les workers si pas déjà fait
    if not queue_manager.running:
        await queue_manager.start_workers()

    # Attendre completion
    success = await queue_manager.wait_completion(timeout=300)  # 5 minutes max

    # Récupérer les résultats
    livres_updated = []
    for i, livre in enumerate(livres):
        task_id = task_ids[i]
        task = queue_manager.completed_tasks.get(task_id) or queue_manager.failed_tasks.get(task_id)

        livre_copy = livre.copy()
        if task and task.status == TaskStatus.COMPLETED:
            livre_copy['description'] = task.result
        else:
            livre_copy['description'] = "Description non trouvée"

        livres_updated.append(livre_copy)

    # Afficher stats finales
    stats = queue_manager.get_stats()
    print(f"📊 STATS FINALES: {stats['completed_tasks']}/{stats['total_tasks']} "
          f"({stats.get('overall_rate', 0):.1f}/s)")

    return livres_updated

if __name__ == "__main__":
    # Test rapide
    async def test():
        livres_test = [
            {'url': 'https://www.amazon.fr/dp/2266292617', 'titre': 'Test 1'},
            {'url': 'https://www.amazon.fr/dp/B07D7GB3MX', 'titre': 'Test 2'}
        ]

        result = await process_descriptions_batch(livres_test)
        print(f"Résultat test: {result}")

    asyncio.run(test())