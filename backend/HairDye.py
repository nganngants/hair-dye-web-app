import torch
from model import BiSeNet
import os
from skimage.filters import gaussian
import os.path as osp
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from resnet import Resnet18

import cv2
class HairDye():
  def __init__(self):
    self.anno = None
  def vis_parsing_maps(self,im, parsing_anno, stride, save_im=False, save_path='vis_results/parsing_map_on_im.jpg'):
      # Colors for all 20 parts
      part_colors = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],
                    [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0],
                    [255, 255, 255],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]

      im = np.array(im)
      vis_im = im.copy().astype(np.uint8)
      vis_parsing_anno = parsing_anno.copy().astype(np.uint8)
      vis_parsing_anno = cv2.resize(vis_parsing_anno, None, fx=stride, fy=stride, interpolation=cv2.INTER_NEAREST)
      vis_parsing_anno_color = np.zeros((vis_parsing_anno.shape[0], vis_parsing_anno.shape[1], 3)) + 255

      num_of_class = np.max(vis_parsing_anno)

      for pi in range(1, num_of_class + 1):
          index = np.where(vis_parsing_anno == pi)
          vis_parsing_anno_color[index[0], index[1], :] = part_colors[pi]

      vis_parsing_anno_color = vis_parsing_anno_color.astype(np.uint8)
      # print(vis_parsing_anno_color.shape, vis_im.shape)
      vis_im = cv2.addWeighted(cv2.cvtColor(vis_im, cv2.COLOR_RGB2BGR), 0.4, vis_parsing_anno_color, 0.6, 0)
      self.anno = vis_parsing_anno
      # Save result or not
        # if save_im:
        #     cv2.imwrite("parsing"+'.png', vis_parsing_anno)
        #     cv2.imwrite("parsing"+".jpg", vis_im, [cv2.IMWRITE_JPEG_QUALITY, 100])

  def get_parsing(self,img,save_path="/content"):
    n_classes = 19
    net = BiSeNet(n_classes=n_classes)
    # PATH = "/content/drive/MyDrive/79999_iter.pth"
    PATH = "./79999_iter.pth"
    net.load_state_dict(torch.load(PATH, map_location=torch.device('cpu')))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    net.to(device)
    net.eval()
    to_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    with torch.no_grad():
      # img = Image.open(img_path)
      img = Image.fromarray(img)
      image = img.resize((512, 512), Image.BILINEAR)
      img = to_tensor(image)
      img = torch.unsqueeze(img, 0)
      #img = img.cuda()
      out = net(img)[0]
      parsing = out.squeeze(0).cpu().numpy().argmax(0)
      self.vis_parsing_maps(image, parsing, stride=1, save_im=True, save_path=save_path)
      return parsing
    
  def sharpen(self,img):
    img = img * 1.0
    gauss_out = gaussian(img, sigma=5, channel_axis=0)

    alpha = 1.5
    img_out = (img - gauss_out) * alpha + img

    img_out = img_out / 255.0

    mask_1 = img_out < 0
    mask_2 = img_out > 1

    img_out = img_out * (1 - mask_1)
    img_out = img_out * (1 - mask_2) + mask_2
    img_out = np.clip(img_out, 0, 1)
    img_out = img_out * 255
    return np.array(img_out, dtype=np.uint8)
  
  def change_v(self, v, mask, target):
    v_mean = np.sum(v * mask) / np.sum(mask)
    alpha = target / v_mean
    x = v / 255
    x = 1 - (1 - x) ** alpha
    v[:] = x * 255
  
  def recolor(self, img, mask, color=(0x40, 0x66, 0x66)):
    color = np.array(color, dtype='uint8', ndmin=3)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    color_hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)
    img_hsv[..., 0] = color_hsv[..., 0]
    self.change_v(img_hsv[..., 2:], mask, color_hsv[..., 2:])
    self.change_v(img_hsv[..., 1:2], mask, color_hsv[..., 1:2])
    hair = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR) * mask
    origin = img * (1 - mask)
    img = (origin + hair).astype(np.uint8)
    return img
  
  def hair(self,image, parsing, part=17, color=[10, 250, 10]):
      if color.startswith('#'):
          # Convert color string "#RRGGBB" to RGB values
          color = color.lstrip('#')
          b, g, r = [int(color[i:i+2], 16) for i in (0, 2, 4)]
      else:
          # Assume color is a list of RGB values
          b, g, r = color

      # tar_color = np.zeros_like(image)
      # tar_color[:, :, 0] = b
      # tar_color[:, :, 1] = g
      # tar_color[:, :, 2] = r

      # image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
      # tar_hsv = cv2.cvtColor(tar_color, cv2.COLOR_BGR2HSV)
      # image_hsv[:, :, 0:1] = tar_hsv[:, :, 0:1]

      # changed = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2BGR)

      # if part == 17:
      #     changed = self.sharpen(changed)

      # changed[parsing != part] = image[parsing != part]
      mask = np.expand_dims(np.array(parsing == part).astype('int64'), axis=-1)
      changed = self.recolor(image, mask, color=(b,g,r)) 
      changed = self.sharpen(changed) 
      changed[parsing != part] = image[parsing != part]
      return changed
  
  def predict(self,img,color):
    # img = cv2.imread(img_path)
    parsing = self.get_parsing(img)
    parsing = cv2.resize(parsing, (img.shape[1],img.shape[0]), interpolation=cv2.INTER_NEAREST)
    new_img = None
    new_img = self.hair(img, parsing,part=17,color=color)
    return new_img
if __name__ == '__main__':
  import pickle
  hairdye = HairDye()
  # Unpickle the object from the file
  with open('HairDye.pkl', 'wb') as file:
        pickle.dump(hairdye, file)
