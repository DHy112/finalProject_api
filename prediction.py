from fastai.vision.all import *
from torch.autograd import Variable
from torchvision.transforms import transforms
from PIL import Image


class ClassificationModel():

    def __init__(self):
        return

    def load(self, model_path, labels_path, eval=False):
        self.model = torch.load(model_path)
        self.model = torch.nn.Sequential(self.model)
        self.labels = open(labels_path, 'r').read().splitlines()

        if eval:
            print(self.model.eval())
        return

    def predict(self, image_path):
        tfms = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor()])

        img = Image.open(image_path)
        tnsr = tfms(img).unsqueeze(0)
        op = self.model(tnsr)
        op_b = torch.round(op)

        op_b_np = torch.Tensor.cpu(op_b).detach().numpy()
        max_index = op_b_np.argmax()
        # preds = np.where(op_b_np == int(op_b_np[0][max_index]))[1]
        preds = np.where(op_b_np == -1)[1]

        sigs_op = torch.Tensor.cpu(torch.round((op) * 100)).detach().numpy()[0]

        o_p = np.argsort(torch.Tensor.cpu(op).detach().numpy())[0][::-1]

        label = []
        for i in preds:
            label.append(self.labels[i])

        return label
