"""The annotation JPEG and source identity must be returned atomically."""
import base64,json,unittest
from urllib.request import build_opener,ProxyHandler
import cv2
import numpy as np
from vision.keypoints.frame_server import LatestFrameServer


class MetadataContract(unittest.TestCase):
    def test_image_and_source_metadata_share_publication(self):
        opener=build_opener(ProxyHandler({}))
        with LatestFrameServer(0) as server:
            for number,color in ((15,(0,0,255)),(93,(0,255,0))):
                server.publish(np.full((720,1280,3),color,np.uint8),number,1234.5,
                               {'sign_recognition':{'label':'三'}})
                with opener.open('http://127.0.0.1:%d/frame.jpg'%server.port) as response:
                    metadata=json.loads(base64.b64decode(response.headers['X-Frame-Metadata']))
                    frame=cv2.imdecode(np.frombuffer(response.read(),np.uint8),cv2.IMREAD_COLOR)
                self.assertEqual(metadata['frame_id'],number)
                self.assertEqual(metadata['source_timestamp_s'],1234.5)
                self.assertEqual(metadata['sign_recognition']['label'],'三')
                self.assertLess(np.max(np.abs(frame[360,640].astype(int)-color)),4)


if __name__=='__main__':unittest.main()
