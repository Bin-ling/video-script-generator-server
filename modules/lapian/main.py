import os
import json
import time
from datetime import datetime
from modules.lapian.shot_analyzer import ShotAnalyzer
from modules.lapian.shot_extractor import extract_all_shots
from modules.lapian.report_generator import generate_report, save_report, generate_markdown_report
from modules.lapian.preprocessor import get_video_info
from app.utils.logger import logger
from app.utils.progress_manager import progress


class VideoLapianTool:
    def __init__(self):
        self.analyzer = ShotAnalyzer()

    def process(self, video_path, output_dir=None, extract_shots=True):
        if output_dir is None:
            timestamp = int(time.time())
            output_dir = os.path.join(os.path.dirname(video_path), f"lapian_{timestamp}")

        os.makedirs(output_dir, exist_ok=True)

        result = {
            'video_path': video_path,
            'output_dir': output_dir,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'processing',
            'analysis_mode': 'direct',
            'steps': {}
        }

        logger.info(f"开始视频拉片分析: {video_path}")

        try:
            progress["percentage"] = 10
            progress["status"] = "获取视频信息"

            video_info = get_video_info(video_path)
            result['steps']['video_info'] = {
                'status': 'success',
                'info': video_info
            }

            progress["percentage"] = 30
            progress["status"] = "AI分析视频中"

            analysis_result = self.analyzer.analyze_video_directly(
                video_path,
                prompt=None,
                script_text="",
                save_result=True,
                output_dir=output_dir
            )

            result['steps']['analysis'] = {
                'status': 'success',
                'total_shots': analysis_result.get('total_shots', 0),
                'analysis_file': os.path.join(output_dir, 'direct_analysis_result.json')
            }

            shots = analysis_result.get('shots', [])

            if extract_shots and shots:
                progress["percentage"] = 60
                progress["status"] = "提取镜头片段"

                try:
                    extraction_result = extract_all_shots(video_path, shots, output_dir)

                    extraction_file = os.path.join(output_dir, 'extraction_results.json')
                    with open(extraction_file, 'w', encoding='utf-8') as f:
                        json.dump(extraction_result, f, ensure_ascii=False, indent=2)

                    result['steps']['extraction'] = {
                        'status': 'success',
                        'extracted_count': len(extraction_result.get('extracted_shots', [])),
                        'failed_count': len(extraction_result.get('failed_shots', [])),
                        'extraction_file': extraction_file
                    }
                except Exception as e:
                    logger.error(f"镜头提取失败: {e}")
                    result['steps']['extraction'] = {
                        'status': 'failed',
                        'reason': str(e)
                    }
            else:
                extraction_result = None
                result['steps']['extraction'] = {
                    'status': 'skipped',
                    'reason': '未启用镜头提取或无镜头数据'
                }

            progress["percentage"] = 80
            progress["status"] = "生成拉片报告"

            report = generate_report(
                video_path,
                shots,
                extraction_result,
                video_info,
                ""
            )

            report_file = os.path.join(output_dir, 'lapian_report.json')
            save_report(report, report_file)

            md_file = os.path.join(output_dir, 'lapian_report.md')
            generate_markdown_report(report, md_file)

            result['steps']['report'] = {
                'status': 'success',
                'report_file': report_file,
                'markdown_file': md_file
            }

            result['status'] = 'completed'
            result['report'] = report

            progress["percentage"] = 100
            progress["status"] = "分析完成"

            return result

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            return result
